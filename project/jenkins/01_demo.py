import os
import jenkins
import xml.etree.ElementTree as ET

jks_host = os.environ.get("JENKINS_URL", "http://localhost:8080")
jks_username = os.environ.get("JENKINS_USER")
jks_password = os.environ.get("JENKINS_TOKEN")
if not jks_username or not jks_password:
    print("错误: 请设置环境变量 JENKINS_USER 和 JENKINS_TOKEN")
    exit(1)


server = jenkins.Jenkins(jks_host, username=jks_username, password=jks_password)
user = server.get_whoami()
version = server.get_version()
print(user)
print(version)


# 获取所有的job
jobs = server.get_jobs()
for job in jobs:
    print(job['name'], server.is_folder(job['name']))
    if job['name'] == "server":
        print(job)

# 获取单个job的配置
job_full_path = "server/game"  # job的完整路径
my_job_config_xml = server.get_job_config(job_full_path)
# print(my_job_config_xml)

print("===============================")
# 解析xml
root = ET.fromstringlist(my_job_config_xml)
description_node = root.find("description")  # 查找描述节点
print(description_node.text)  # 打印节点信息
# 示例修改节点配置
# 节点路径：sources/data/jenkins.branch.BranchSource/source/traits/jenkins.scm.impl.trait.RegexSCMHeadFilterTrait/regex
xpath_query = ".//jenkins.scm.impl.trait.RegexSCMHeadFilterTrait/regex"
regex_node = root.find(xpath_query)
if regex_node is not None:
    old_regex = regex_node.text
    # 设置新的内容
    new_regex = "^5117$|^5102$|^5342$|^5332$|^5312$"
    regex_node.text = new_regex
    print(f'检测到旧正则: {old_regex}')
    print(f'准备更新位: {new_regex}')

    # 转换为字符串，并推送回 jenkins
    updated_xml = ET.tostring(root, encoding='unicode')
    server.reconfig_job(job_full_path, updated_xml)
    print("✅ Job 配置更新成功！")
else:
    print("❌ 未能在 XML 中找到 RegexSCMHeadFilterTrait 节点，请检查路径。")

# # 修改完成，触发build，用于扫描多分支流水线
# server.build_job_url(job_full_path)


