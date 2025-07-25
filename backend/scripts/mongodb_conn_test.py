from pymongo import MongoClient
client = MongoClient("mongodb+srv://tharunbejawada18:YII77Cg8QE6YJ56t@kodekloudcluster.jnokue4.mongodb.net/KodeKloudCluster?retryWrites=true&w=majority")
client.list_database_names()  # should not raise error
