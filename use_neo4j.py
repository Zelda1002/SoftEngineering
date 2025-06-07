import client_hw
from py2neo import Graph
from dotenv import load_dotenv
load_dotenv()


# Neo4j连接
uri = "bolt://119.3.225.124:7687"
user = "neo4j"
password = "1234qwer"


# 连接neo4j
def connect_neo4j():
    try:
        graph = Graph(uri, auth=(user, password))
        graph.run("MATCH () RETURN 1 LIMIT 1")
        print("Neo4j 连接成功")
        return graph
    except Exception as e:
        print(f"Neo4j 连接失败:{str(e)}")
        raise


# 调用api识别实体，从neo4j中查询
def query_from_neo4j(user_input):
    # 调用api提取实体
    system_content = "你是一个有用的软件工程课程助手,请从用户提供的语句里提取实体，仅返回提取结果，不同实体间用逗号分割"
    user_content = user_input
    response = client_hw.get_model_response(system_content, user_content)
    entities = response.split(",")
    entity_result_set = set()
    try:
        graph = connect_neo4j()
    except Exception as e:
        print(f"neo4j连接失败：{str(e)}")
        return entity_result_set
    for entity in entities:
        # Cypher查询：匹配实体作为起点或终点的所有直接关系
        query = """
            MATCH (start)-[r]->(end)
            WHERE start.name = $entity OR end.name = $entity
            RETURN start.name AS 起始节点,
                   end.name AS 终止节点
        """
        try:
            # 执行查询
            result = graph.run(query, parameters={"entity": entity})
            records = result.data()
            for idx in records:
                entity_result_set.add(idx['起始节点'])
                entity_result_set.add(idx['终止节点'])
        except Exception as e:
            print(f"查询实体 '{entity}' 时发生错误: {str(e)}")
    entity_result_set = {i for i in entity_result_set if i is not None}
    return entity_result_set
