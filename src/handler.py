#!/usr/bin/env python
# encoding: utf-8

# Common Lib
from aws_common import *

# General Lib
# Additional Lib

# User Lib
from h_conf import *
from h_backup_glue_catalog import *
#####  #####  #####  #####

# Main Function
def m_backup(event, context):
    # Backup AWS Glue Databases and Tables
    backup_aws_glue_data_catalog()
    logging.debug("SUCCESS: BACKUP AWS GLUE DATABASE & TABLE")

    # Backup AWS Glue Connections
    backup_aws_glue_connections()
    logging.debug("SUCCESS: BACKUP AWS GLUE CONNECTION")

    # Backup AWS Glue Crawler
    backup_aws_glue_crawlers()
    logging.debug("SUCCESS: BACKUP AWS GLUE CRAWLER")
    return respond(StatusCode=200, Body={'input': None, 'output': {'BackupDate': strtime}, 'body': None})

def m_restore(event, context):
    BackupDate = event['pathParameters']['BackupDate'] # e.g. '2021-01-06-05-30-27'
    
    # Restore AWS Glue Databases and Tables
    restore_aws_glue_data_catalog(BackupDate=BackupDate)
    logging.debug("SUCCESS: RESTORE AWS GLUE DATABASE & TABLE")

    # Restore AWS Glue Connections
    restore_aws_glue_connections(BackupDate=BackupDate)
    logging.debug("SUCCESS: RESTORE AWS GLUE CONNECTION")
    return respond(StatusCode=200, Body={'input': {'BackupDate': BackupDate}, 'output': None, 'body': None})

if __name__ == "__main__":
    m_backup('', '')
    # m_restore('', '')
