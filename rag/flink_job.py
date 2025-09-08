import os
import time
import logging
from pyflink.table import EnvironmentSettings, StreamTableEnvironment
from pyflink.table.udf import udf
from pyflink.table import DataTypes
from rag_pipeline import RagPipeline
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FlinkMain")

def main():
    env_settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(environment_settings=env_settings)
    
    jar_path = "file:///Users/akhileshkumar/flink-libs/flink-sql-connector-kafka-3.1.0-1.18.jar"
    t_env.get_config().get_configuration().set_string("pipeline.jars", jar_path)
    t_env.get_config().get_configuration().set_string("parallelism.default", "1")
    
    t_env.get_config().get_configuration().set_string("python.logging.level", "INFO")
    t_env.get_config().get_configuration().set_string("taskmanager.memory.process.size", "1024m")    
    source_ddl = """
    CREATE TABLE user_queries (
        user_id STRING,
        query_text STRING,
        timestamp_ms BIGINT,
        proctime AS PROCTIME()
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'finance-chat-queries',
        'properties.bootstrap.servers' = 'localhost:9092',
        'properties.group.id' = 'finance-rag-group',
        'properties.auto.offset.reset' = 'latest',
        'format' = 'json'
    )
    """
    sink_ddl = """
    CREATE TABLE rag_results (
        user_id STRING,
        query_text STRING,
        ai_response STRING,
        process_time TIMESTAMP(3)
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'finance-rag-results',
        'properties.bootstrap.servers' = 'localhost:9092',
        'format' = 'json',
        'properties.transaction.timeout.ms' = '900000',
        'properties.max.request.size' = '2097152',
        'sink.parallelism' = '1'
    )
    """

    t_env.execute_sql(source_ddl)
    
    t_env.execute_sql(sink_ddl)

    t_env.create_temporary_system_function("RagPipeline", udf(RagPipeline(), result_type=DataTypes.STRING()))
    
    t_env.from_path("user_queries").print_schema()
    
    t_env.from_path("rag_results").print_schema()
    
    processing_query = """
    INSERT INTO rag_results
    SELECT
        user_id,
        query_text,
        RagPipeline(query_text) AS ai_response,
        CURRENT_TIMESTAMP AS process_time
    FROM user_queries
    WHERE query_text IS NOT NULL 
      AND CHAR_LENGTH(query_text) > 0
      AND user_id IS NOT NULL
    """
    
    logger.info("Submitting Flink streaming job...")
    logger.info(f"Processing query: {processing_query}")
    
    try:
        table_result = t_env.execute_sql(processing_query)
        job_client = table_result.get_job_client()
        
        if job_client is not None:
            try:
                job_id = job_client.get_job_id()
                logger.info(f"Job submitted successfully (job_id={job_id})")
                
                job_status = job_client.get_job_status()
                logger.info(f"Job status: {job_status}")
                
                while True:
                    time.sleep(30)  
                    try:
                        current_status = job_client.get_job_status()
                        logger.info(f"Current job status: {current_status}")
                        
                        if str(current_status) in ['FAILED', 'CANCELED', 'FINISHED']:
                            logger.error(f"Job terminated with status: {current_status}")
                            break
                            
                    except Exception as status_check_error:
                        logger.warning(f"Could not check job status: {status_check_error}")
                        
            except Exception as job_error:
                logger.error(f"Job submission error: {job_error}")
        else:
            logger.error("No JobClient returned - job submission may have failed")
            
    except Exception as execution_error:
        logger.error(f"Job execution failed: {execution_error}")
        raise

if __name__ == "__main__":
    main()