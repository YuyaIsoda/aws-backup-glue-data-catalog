#!/usr/bin/env python
# encoding: utf-8

# Common Lib
from aws_common import *

# General Lib
import boto3

# Additional Lib

# User Lib
from h_conf import *
#####  #####  #####  #####

# AWS Services
## AWS Glue: Data Catalog
glue = boto3.client('glue')

def glue_get_databases():
    res = glue.get_databases()
    glue_database_list = res['DatabaseList']
    while 'NextToken' in res:
        res = glue.get_databases(NextToken=res['NextToken'])
        glue_database_list += res['DatabaseList']
    return glue_database_list

def glue_create_database(DatabaseInput):
    try:
        res = glue.create_database(DatabaseInput=DatabaseInput)
        logging.debug("GLUE Database: CREATE: " + DatabaseInput['Name'])
    except glue.exceptions.AlreadyExistsException:
        logging.info("GLUE Database: AlreadyExists: " + DatabaseInput['Name'])
    return None

def glue_get_tables(DatabaseName):
    res = glue.get_tables(DatabaseName=DatabaseName)
    glue_table_list = res['TableList']
    while 'NextToken' in res:
        res = glue.get_tables(DatabaseName=DatabaseName, NextToken=res['NextToken'])
        glue_table_list += res['TableList']
    return glue_table_list

def glue_get_table_versions(DatabaseName, TableName):
    res = glue.get_table_versions(DatabaseName=DatabaseName, TableName=TableName)
    table_version_list = res['TableVersions']
    while 'NextToken' in res:
        res = glue.get_table_versions(DatabaseName=DatabaseName, TableName=TableName, NextToken=res['NextToken'])
        table_version_list += res['TableVersions']
    return table_version_list

def glue_create_table(DatabaseName, TableInput):
    try:
        res = glue.create_table(DatabaseName=DatabaseName, TableInput=TableInput)
        logging.debug("GLUE Table: Create: " + TableInput['Name'])
    except glue.exceptions.AlreadyExistsException:
        logging.info("GLUE Table: AlreadyExists: " + TableInput['Name'])
    return None

def glue_get_connections():
    res = glue.get_connections(HidePassword=False)
    ConnectionList = res['ConnectionList']
    while 'NextToken' in res:
        res = glue.get_connections(HidePassword=False, NextToken=res['NextToken'])
        ConnectionList += res['ConnectionList']
    return ConnectionList

def glue_create_connection(ConnectionInput):
    try:
        res = glue.create_connection(ConnectionInput=ConnectionInput)
        logging.debug("GLUE Connection: Create: " + ConnectionInput['Name'])
    except glue.exceptions.AlreadyExistsException:
        logging.info("GLUE Connection: AlreadyExists: " + ConnectionInput['Name'])
    return None

def glue_get_crawlers():
    res = glue.get_crawlers()
    CrawlerList = res['Crawlers']
    while 'NextToken' in res:
        res = glue.get_crawlers(NextToken=res['NextToken'])
        CrawlerList += res['Crawlers']
    return CrawlerList

## AWS S3
s3 = boto3.client('s3')
s3r = boto3.resource('s3')

def s3_put_object(Bucket, Key, Body):
    res = s3.put_object(Bucket=Bucket, Key=Key, Body=Body)
    return res

def s3_get_object(Bucket, Key):
    try:
        obj = s3r.Object(Bucket, Key)
        body = obj.get()['Body'].read().decode('utf-8')
    except s3.exceptions.NoSuchKey as e:
        logging.info('NoSuchKey : ' + Key)
        return None
    return json.loads(body)

# Backup AWS Glue Data Catalog
def backup_aws_glue_data_catalog():
    # Backup Glue Data Catalog: Databases
    dbs = glue_get_databases()
    Key = "backup/aws_glue/data_catalog/" + strtime + "/databases.json"
    s3_put_object(Bucket=Bucket, Key=Key, Body=json_dumps(data=dbs))

    # Backup Glue Data Catalog: Tables
    for db in dbs:
        # Backup Glue Data Catalog: Tables (Current)
        tbls = glue_get_tables(DatabaseName=db['Name'])
        Key = "backup/aws_glue/data_catalog/" + strtime + "/tables_" + db['Name'] + ".json"
        s3_put_object(Bucket=Bucket, Key=Key, Body=json_dumps(data=tbls))

        # Backup Glue Data Catalog: Tables (all versions)
        versions_list = []
        for tbl in tbls:
            vers = glue_get_table_versions(DatabaseName=db['Name'], TableName=tbl['Name'])
            if len(versions_list) == 0:
                versions_list = vers
            else:
                versions_list += vers
        Key = "backup/aws_glue/data_catalog/" + strtime + "/all_version_tables_" + db['Name'] + ".json"
        s3_put_object(Bucket=Bucket, Key=Key, Body=json_dumps(data=versions_list))
    return dbs

def backup_aws_glue_connections():
    # Backup Glue Data Catalog: Connection
    cons = glue_get_connections()
    Key = "backup/aws_glue/data_catalog/" + strtime + "/connections.json"
    s3_put_object(Bucket=Bucket, Key=Key, Body=json_dumps(data=cons))
    return cons

def backup_aws_glue_crawlers():
    # Backup Glue Data Catalog: Crawlers
    crws = glue_get_crawlers()
    Key = "backup/aws_glue/data_catalog/" + strtime + "/crawlers.json"
    s3_put_object(Bucket=Bucket, Key=Key, Body=json_dumps(data=crws))
    return crws

# Restore AWS Glue Data Catalog
def reformat(obj, del_list):
    for i in del_list:
        if i in obj:
            del obj[i]
    return obj

def restore_aws_glue_data_catalog(BackupDate):
    # Restore AWS Glue Data Catalog: Databases
    Key = "backup/aws_glue/data_catalog/" + str(BackupDate) + "/databases.json"
    dbs = s3_get_object(Bucket=Bucket, Key=Key)
    if dbs == None:
        return None
        
    del_list = ['CreateTime', 'CatalogId']
    for db in dbs:
        db = reformat(db, del_list)
        glue_create_database(DatabaseInput=db)

        # Restore AWS Glue Data Catalog: Tables
        Key = "backup/aws_glue/data_catalog/" + str(BackupDate)  + "/tables_" + db['Name'] + ".json"
        tbls = s3_get_object(Bucket=Bucket, Key=Key)
        if tbls == None:
            continue
            
        del_list = ['CatalogId', 'DatabaseName', 'LastAccessTime', 'CreateTime', 'UpdateTime', 'CreatedBy', 'IsRegisteredWithLakeFormation']
        for tbl in tbls:
            tbl = reformat(tbl, del_list)
            glue_create_table(DatabaseName=db['Name'], TableInput=tbl)
    return dbs

def restore_aws_glue_connections(BackupDate):
    # Restore AWS Glue Data Catalog: Connections
    Key = "backup/aws_glue/data_catalog/" + str(BackupDate) + "/connections.json"
    cons = s3_get_object(Bucket=Bucket, Key=Key)
    if cons == None:
        return None
        
    del_list = ['CreationTime', 'LastUpdatedTime', 'LastUpdatedBy']
    for con in cons:
        con = reformat(con, del_list)
        glue_create_connection(ConnectionInput=con)
    return cons
