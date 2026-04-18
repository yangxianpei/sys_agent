# openapi_json = {
#     "openapi": "3.1.0",
#     "info": {"title": "IP API", "version": "1.0"},
#     "servers": [{"url": "http://ip-api.com"}],
#     "paths": {
#         "/json": {
#             "get": {
#                 "summary": "查询IP信息",
#                 "description": "获取IP的地理位置",
#                 "parameters": [
#                     {
#                         "name": "query",
#                         "in": "query",
#                         "required": False,
#                         "schema": {"type": "string"},
#                     }
#                 ],
#                 "responses": {"200": {"description": "OK"}},
#             }
#         }
#     },
# }


# openapi_json = {
#     "openapi": "3.1.0",
#     "info": {"title": "Joke API", "version": "1.0"},
#     "servers": [{"url": "https://v2.jokeapi.dev"}],
#     "paths": {
#         "/joke/Any": {
#             "get": {
#                 "summary": "获取笑话",
#                 "description": "随机返回一条笑话",
#                 "parameters": [],
#                 "responses": {"200": {"description": "OK"}},
#             }
#         }
#     },
# }


# openapi_json = {
#     "openapi": "3.1.0",
#     "info": {
#         "title": "Rainbow Praise API",
#         "description": "生成彩虹屁夸人语句",
#         "version": "1.0",
#     },
#     "servers": [{"url": "https://api.shadiao.pro"}],
#     "paths": {
#         "/chp": {
#             "get": {
#                 "summary": "生成彩虹屁",
#                 "description": "返回一句夸人的彩虹屁",
#                 "parameters": [],
#                 "responses": {"200": {"description": "成功返回彩虹屁文本"}},
#             }
#         }
#     },
# }


默认工具