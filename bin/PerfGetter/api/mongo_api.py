#!/usr/bin/python
# --encoding:utf-8--

from mongo_driver import db_handler
from logger import logger

class MongoBase(object):
    def __init__(self):
        self.auto_id_field = "auto_inc_count"
    
    def init_auto_inc(self, collection):
        '''
        初始化内部计数器
        '''
        if not self.get_collection(collection).find_one({'f_type': self.auto_id_field}):
            self.get_collection(collection).insert({'f_type': self.auto_id_field, 'value': 0})
    
    def get_auto_inc(self, collection):
        '''
        返回计数器的值
        '''
        auto_inc = self.get_collection(collection).find_one({'f_type': self.auto_id_field})
        if auto_inc:
            return auto_inc['value']
    
    def update_inc(self, collection):
        '''
        更新计数器
        '''
        self.get_collection(collection).update({'f_type': self.auto_id_field}, {"$inc": {'value': 1}})


class MongoExecuter(MongoBase):
    def __init__(self, db_handler):
        self.db_handler = db_handler
        super(MongoExecuter, self).__init__()
    
    def get_collection(self, collection):
        '''
        返回DB的集合
        '''
        if not isinstance(collection, str) and not isinstance(collection, unicode):
            error = RuntimeError("Get Collection Error: need string argument")
            logger.exception(error)
            raise error
        try:
            collection = getattr(self.db_handler, collection)
            return collection
        except Exception, e:
            logger.exception(e)
            raise
    
    def count(self, collection):
        '''
        计算集合总的数据
        '''
        return self.get_collection(collection).count()

    def query(self, collection, conditions, fields=dict(), exclude_oid=True):
        '''
        在collection上执行一个查询
        作为一个生成器，返回查询到的记录
        '''
        if exclude_oid:
            fields.setdefault('_id', False)
        return self.get_collection(collection).find(conditions, fields)
    
    def query_one(self, collection, conditions, fields=dict(), exclude_oid=True):
        '''
        在collection上执行一个查询
        作为字典，返回查询到的记录
        '''
        if exclude_oid:
            fields.setdefault('_id', False)
        return self.get_collection(collection).find_one(conditions, fields)
    
    def query_all(self, collection):
        '''
        在collection上执行一个查询
        返回除了计数器以外的所有记录
        '''
        return self.query(collection, {'f_type': {"$exists": False}})
    
    
    def query_limit(self, collection, page_num, num_per_page, conditions, fields):
        '''
        模拟分页
        '''
        page_num = 0 if not page_num else page_num
        num_per_page = 0 if not num_per_page else num_per_page
        if page_num <= 0 or not isinstance(page_num, int):
           error = RuntimeError("Invalid type of argument page_num, need int and must more than 1.")
           logger.exception(error)
           raise error
        if num_per_page <= 0 or not isinstance(num_per_page, int):
           error = RuntimeError("Invalid type of argument num_per_page, need int and must more than 1.")
           logger.exception(error)
           raise error
        
        collection = self.get_collection(collection)
        if page_num == 1:
            return collection.find(kwargs).limit(num_per_page)
        else:
            return collection.find(kwargs).skip((page_num - 1) * num_per_page).limit(num_per_page)

    def insert(self, collection, contents):
        '''
        插入记录 返回记录的ObjectID
        '''
        inc_id = self.get_auto_inc(collection)
        self.update_inc(collection)
        contents.setdefault("id", inc_id)
        obj_id = self.get_collection(collection).insert(contents)
        return obj_id
    
    def update(self, collection, condition, contents):
        '''
        更新记录
        condition为条件，是一个字典
        contents为需要更新的内容
        '''
        if not condition or not isinstance(condition, dict):
            error = RuntimeError("Need *condition* parameter")
            logger.exception(error)
            raise error
        self.get_collection(collection).update(condition, {"$set": contents})
    
    def find_modify(self, collection, query, update=None,
                    sort=None, upsert=False, full_response=True, **kwargs):
        '''
        封装MongoDb的findAndModify
        '''
        kwargs.setdefault('new', True)
        return self.get_collection(collection).find_and_modify(query, update, sort,
                                                        upsert, full_response, **kwargs)

    def delete(self, collection, conditions):
        '''
        删除指定的记录
        '''
        self.get_collection(collection).remove(conditions)
    
    def clear(self, collection):
        '''
        清除集合内的所有数据
        '''
        self.get_collection(collection).remove()
    

