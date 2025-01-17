import requests
import json
import time
import random

# 预定义头
headers = dict()
headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
headers['Host'] = 'weiban.mycourse.cn'
headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
headers['Accept-Language'] = 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'
headers['Accept-Encoding'] = 'gzip, deflate, br'

with open('answer.json', 'r') as f:
    right_answer = json.loads(f.read())

class SleepSetting:
    def __init__(self):
        self.sleep_between_course = 1
        self.sleep_begin_and_end = 39
        self.sleep_between_question = 3
        self.sleep_question_range = 6
_sleepSetting = SleepSetting()

class Weiban:
    def __init__(self, cookies=None, data='', sleepSetting=None):
        # 设置睡眠时间
        if sleepSetting is None:
            sleepSetting = _sleepSetting
        self.sleepSetting = sleepSetting

        # 预处理cookies
        if cookies is None:
            cookies = dict()
        self.cookies = cookies

        # 预处理data
        if not data:
            data = input('输入data: ')
        key_values = data.split('&')
        data = dict()
        for key_value in key_values:
            key, value = key_value.split('=')
            data[key] = value
        self.data = data

        # 占位符
        self.categoryList = []
        self.unFinishedCourseList = []
        self.examList = []

        # url
        self.urlListCategory = 'https://weiban.mycourse.cn/pharos/usercourse/listCategory.do?timestamp=%s'
        self.urlListCourse = 'https://weiban.mycourse.cn/pharos/usercourse/listCourse.do?timestamp=%s'
        self.urlStudy = 'https://weiban.mycourse.cn/pharos/usercourse/study.do?timestamp=%s'
        self.urlFinish = 'https://weiban.mycourse.cn/pharos/usercourse/finish.do?callback=jQuery16408245967680834043_1611063154388&userCourseId=%s&tenantCode=%s&_=%s'
        self.urlListexam = 'https://weiban.mycourse.cn/pharos/exam/listPlan.do?timestamp=%s'
        self.urlPrepareExam = 'https://weiban.mycourse.cn/pharos/exam/preparePaper.do?timestamp=%s'
        self.urlStartExam = 'https://weiban.mycourse.cn/pharos/exam/startPaper.do?timestamp=%s'
        self.urlRecordQuestion = 'https://weiban.mycourse.cn/pharos/exam/recordQuestion.do?timestamp=%s'
        self.urlFinishExam = 'https://weiban.mycourse.cn/pharos/exam/submitPaper.do?timestamp=%s'

        # Session 初始化
        self.s = requests.Session()
        self.s.headers.update(headers)
        requests.utils.add_dict_to_cookiejar(self.s.cookies, self.cookies)

    def sleep(self, t):
        for i in range(t):
            print('%d/%d' % (i+1, t), end='\r')
            time.sleep(1)
        print()

    def getCategory(self):
        url = self.urlListCategory % get_time()
        data = {
                'userProjectId': self.data['userProjectId'],
                'chooseType': 3,
                'userId': self.data['userId'],
                'tenantCode': self.data['tenantCode'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        self.categoryList = resp.json()['data']
        # 输出状态：
        for category in self.categoryList:
            print('%s %s %d/%d' % (
                category['categoryCode'],
                category['categoryName'],
                category['finishedNum'],
                category['totalNum']
                )
            )

    def fetchUnFinishedCourse(self):
        for category in self.categoryList:
            if category['finishedNum'] < category['totalNum']:
                print('获取%s课程列表' % category['categoryCode'])
                self.fetchCourseList(category=category)

    def fetchCourseList(self, category):
        categoryCode = category['categoryCode']
        url = self.urlListCourse % get_time()
        data = {
                'userProjectId': self.data['userProjectId'],
                'chooseType': 3,
                'categoryCode': categoryCode,
                'name': "",
                'userId': self.data['userId'],
                'tenantCode': self.data['tenantCode'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        courseList = resp.json()['data']
        for course in courseList:
            if course['finished'] == 2:
                self.unFinishedCourseList.append(course)

    def doCourse(self, course):
        print('进入课程%s，' % course['resourceName'], end='')
        url = self.urlStudy % get_time()
        data = {
                'courseId': course['resourceId'],
                'userProjectId': self.data['userProjectId'],
                'tenantCode': self.data['tenantCode'],
                'userId': self.data['userId'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        status = resp.json()['code']
        print('返回状态代码%s' % status)
        
        self.sleep(self.sleepSetting.sleep_begin_and_end)

        url = self.urlFinish % (
                course['userCourseId'],
                self.data['tenantCode'],
                int(time.time() * 1000)
                )
        resp = self.s.get(url=url)
        print('结束HTTP状态码%s' % resp.status_code)
        return resp

    def flash(self):
        self.getCategory()
        self.fetchUnFinishedCourse()
        finishedCoursesCounter = 0
        for course in self.unFinishedCourseList:
            self.doCourse(course)
            finishedCoursesCounter += 1
            print('状态 已完成: %s, 剩余: %s' % (finishedCoursesCounter, len(self.unFinishedCourseList)))
            self.sleep(self.sleepSetting.sleep_between_course)

    def flashExam(self):
        url = self.urlListexam % get_time()
        data = {
                'userProjectId': self.data['userProjectId'],
                'tenantCode': self.data['tenantCode'],
                'userId': self.data['userId'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        self.examList = resp.json()['data']
        print('检测到%s个考试' % str(len(self.examList)))
        for exam in self.examList:
            self.doExam(exam)

    def doExam(self, exam):
        url = self.urlPrepareExam % get_time()
        data = {
                'userExamPlanId': exam['id'],
                'tenantCode': self.data['tenantCode'],
                'userId': self.data['userId'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        status = resp.json()['code']
        print('准备考试，返回状态%s' % status)
        url = self.urlStartExam % get_time()
        data = {
                'userExamPlanId': exam['id'],
                'tenantCode': self.data['tenantCode'],
                'userId': self.data['userId'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        resp_json = resp.json()
        status = resp_json['code']
        print('开始答题，服务器状态%s' % status)
        question_list = resp_json['data']
        n = 1
        for question in question_list:
            question_id = question['id']
            answer_id = right_answer[question_id]

            random_use_time = self.sleepSetting.sleep_between_question+random.randint(0, self.sleepSetting.sleep_question_range)
            self.sleep(random_use_time)

            url = self.urlRecordQuestion % get_time()
            data = {
                    'userExamPlanId': exam['id'],
                    'questionId': question_id,
                    'useTime': random_use_time,
                    'answerIds': answer_id,
                    'tenantCode': self.data['tenantCode'],
                    'userId': self.data['userId'],
                    'token': self.data['token'],
                    }
            resp = self.s.post(url=url, data=data)
            status = resp.json()['code']
            print('正在做第%d题，状态%s' % (n, status), end='\r')
            n += 1
        print('开始提交考试')
        url = self.urlFinishExam % get_time()
        data = {
                'userExamPlanId': exam['id'],
                'tenantCode': self.data['tenantCode'],
                'userId': self.data['userId'],
                'token': self.data['token'],
                }
        resp = self.s.post(url=url, data=data)
        print('服务器返回以下状态')
        print(resp.content)
        



def get_time():
    return str(int(time.time() - 1))

def main():
    hint = input('输入学号: ')
    weiban = Weiban()
    weiban.flash()
    weiban.flashExam()
    print(hint, '完成')

if __name__ == '__main__':
    main()
