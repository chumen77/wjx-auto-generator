import os 
import sys
from multiprocessing import cpu_count, Process
import time
import random
import shutil
import hashlib
import subprocess
import logging
debug=False
warn_num=375
def check_update(server:str):
    import requests
    version=1.1
    zip_version=1.0
    branch="raspberrypi"
    address=server+"/zhanghua000/wjx-auto-generator-env/raw/"+branch+"/version.json"
    try:
        response=requests.get(address)
        version_inf=response.json()
    except:
        logger.error("检查更新失败")
        return -1
    if version_inf["version"]>version:
        logger.info("已发现脚本更新")
        ans=input("是否下载新版本？(Y/n)").lower()
        if ans=="n":
            return 2
        if branch!=version_inf["branch"]:
            logger.error("升级信息中的分支与实际分支不符")
            return 4
        r=requests.get(server+"/zhanghua000/wjx-auto-generator/raw/"+str(version_inf["branch"])+"/wjx.py")
        shutil.copy("wjx.py","wjx.py.bak")
        with open("wjx.py","w",encoding="utf-8") as updater:
            updater.write(r.read)
        with open("wjx.py","rb") as md5_checker:
            md5=hashlib.md5(md5_checker.read()).hexdigest()
            if md5!=version_inf["scr_md5"]:
                logging.error("MD5验证失败，取消本次更新")
                shutil.move("wjx.py.bak","wjx.py")
                return 1
    else:
        logger.info("未发现脚本更新")
    return 0
def do_survey(url_2:str,logger_:logging.Logger):
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions
    browser=webdriver.FirefoxOptions()
    profile=webdriver.FirefoxProfile()
    if debug==False:
        browser.add_argument("--headless")
    profile.set_preference("general.useragent.override","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36")
    driver = webdriver.Firefox(options=browser,firefox_profile=profile,service_log_path="log/driver.log")
    driver.get(url_2)
    wait = WebDriverWait(driver, 10)
    element = wait.until(expected_conditions.element_to_be_clickable((By.ID,'submit_button')))
    def do_queue(driver_=driver,logger_=logger_):
        root_element=driver_.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[2]/fieldset")
        question_elements=root_element.find_elements_by_class_name("div_question")
        def gen_str(num:int):
            import string
            return ''.join(random.sample(string.ascii_letters + string.digits, num))
        for element in question_elements:
            element_pos=question_elements.index(element)
            question_title=element.find_element_by_xpath("./div[1]/div[2]").text
            question_answers=element.find_elements_by_xpath("./div[2]/ul/li")
            if question_answers[0].find_element_by_xpath("./input").get_attribute("type")=="radio":
                targets=random.sample(question_answers,1)
                choose_answer_title=targets[0].find_element_by_tag_name("label").text
                targets[0].find_element_by_tag_name("a").click()
                time.sleep(random.randint(1,3))
            elif question_answers[0].find_element_by_tag_name("input").get_attribute("type")=="checkbox":
                choose_num=random.randint(2,len(question_answers))
                choose_answers=[]
                choose_answers_pos=[]
                choose_answer_title=""
                targets=random.sample(question_answers,choose_num)
                for target in targets:
                    choose_answers.append(target)
                    choose_answers_pos.append(question_answers.index(target))
                for answer in choose_answers:
                    text=""
                    answer.find_element_by_tag_name("a").click()
                    choose_answer_title=answer.find_element_by_tag_name("label").text
                    if len(answer.find_elements_by_tag_name("input"))==2:
                        text_input=answer.find_elements_by_tag_name("input")[1]
                        text_input.click()
                        text_input.clear()
                        text=gen_str(random.randint(5,10))
                        text_input.send_keys(text)
                        choose_answer_title=choose_answer_title+text+"\n"
                    else:
                        choose_answer_title=choose_answer_title+"\n"
                    time.sleep(random.randint(1,3))
            elif question_answers[0].find_element_by_xpath("./input").get_attribute("type")=="text":
                target=question_answers[0]
                target.click()
                target.clear()
                text=gen_str(random.randint(10,20))
                target.send_keys(text)
                choose_answer_title=text+"\n"
            else:
                raise RuntimeError("无法获取正确的元素，请重试！")
            logger_.info("选择内容：\n问题："+question_title+"\n选择："+choose_answer_title+"\n")
    do_queue(driver_=driver)
    time.sleep(random.randint(1,3))
    driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[4]/table/tbody/tr/td/input").click()
    try:
        target=driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[4]/div[1]/div[1]/div[1]/div[1]/div[1]")
    except NoSuchElementException:
        logger_.info("未找到验证元素，看起来没有触发验证")
        logger_.info("已提交记录")
        driver.quit()
        return True
    else:
        logger_.warning("找到验证元素，似乎已经触发验证，已记录失败次数")
        if target.get_attribute("id")=="SM_BTN_1":
            def bypass_captcha(driver_,element_):
                return False
            status=bypass_captcha(driver_=driver,element_=target)
        driver.quit()
        return False
def multicoreproc(id_:int,url_:str,times:int,log_level:int):
    max_conn=3
    failed_num=0
    thread_logger=logging.getLogger("thread_logger_"+str(id_))
    files_handler=logging.FileHandler(filename="log/"+str(id_)+".log",mode="w",encoding="utf-8",delay=True)
    files_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s",datefmt="%Y-%m-%d %H:%M:%S"))
    files_handler.setLevel(log_level)
    thread_logger.addHandler(files_handler)
    if times>0:
        if times<=max_conn:
            for time0 in range(times):
                if do_survey(url_2=url_,logger_=thread_logger)==False:
                    failed_num=failed_num+1
                    thread_logger.error("线程 %d 第 %d 次提交失败" %(id_,time0))
                else:
                    thread_logger.info("线程 %d 第 %d 次提交成功" %(id_,time0))
                time.sleep(random.randint(1,3))
        else:
            times1,more_times=divmod(times,max_conn)
            if more_times!=0:
                for time1 in range(more_times):
                    if do_survey(url_2=url_,logger_=thread_logger)==False:
                        failed_num=failed_num+1
                        thread_logger.error("线程 %d 第 %d 次提交失败" %(id_,time1))
                    else:
                        thread_logger.info("线程 %d 第 %d 次提交成功" %(id_,time1))
                    time.sleep(random.randint(1,3))
            for time2 in range(times1):
                for conn in range(max_conn):
                    if do_survey(url_2=url_,logger_=thread_logger)==False:
                        failed_num=failed_num+1
                        thread_logger.error("线程 %d 第 %d 组第 %d 次提交失败" %(id_,time2,conn))
                    else:
                        thread_logger.info("线程 %d 第 %d 组第 %d 次提交成功" %(id_,time2,conn))
                    time.sleep(random.randint(1,3))
                time.sleep(random.randint(3,5))
    else:
        raise ValueError("执行次数必须为正整数")
    if failed_num!=0:
        pause_time=random.randint(10,60)
        thread_logger.warning("线程 %d 失败 %d 次，等待 %2d 秒后将继续补齐失败次数" %(id_,failed_num,pause_time))
        times=failed_num
        time.sleep(pause_time)
        multicoreproc(id_=id_,url_=url_,times=times,log_level=log_level)
    thread_logger.info("线程 %d 结束运行" %id_)
if __name__=="__main__":
    if debug==True:
        log_level=logging.DEBUG
    else:
        log_level=logging.INFO
    os.chdir(os.path.split(os.path.realpath(__file__))[0])
    if os.path.exists("log")==True:
        shutil.rmtree("log")
    os.mkdir("log")
    logger=logging.getLogger()
    logger.setLevel(log_level)
    formatter=logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
    console=logging.StreamHandler()
    console.setFormatter(formatter)
    files_=logging.FileHandler(filename="log/main.log",mode="w",encoding="utf-8")
    files_.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(files_)
    res=check_update("https://hub.fastgit.org")
    if res==-1:
        logger.error("下载版本信息失败")
    elif res==0:
        logger.info("更新成功")
    elif res==1:
        logger.error("文件下载出错，验证失败")
    elif res==2:
        logger.warning("更新已被用户取消")
    elif res==3:
        logger.info("未发现更新")
    elif res==4:
        logger.error("检查更新过程出现错误")
    else:
        raise ValueError("意料之外的返回值")
    times=int(input("请输入生成的问卷的份数："))
    if times>=warn_num:
        logger.warning("当前问卷份数较多，大于 %s 次，较易出现验证。" %warn_num)
    print("问卷星地址举例：https://www.wjx.cn/jq/89714348.aspx")
    url=str(input("请输入问卷星创建的问卷地址："))
    url="https://www.wjx.cn/jq/"+url.split("/")[-1].replace(" ","")
    logger.info("转换地址完成，为："+url)
    start_time=time.time()
    threads=[]
    thread_num=int(cpu_count()/2)
    times_,more_times_=divmod(times,thread_num)
    if more_times_!=0:
        more_thread=Process(target=multicoreproc,args=(thread_num+1,url,more_times_,log_level))
        more_thread.start()
        threads.append(more_thread)
    if times_!=0:
        for thread_id in range(thread_num):
            thread=Process(target=multicoreproc,args=(thread_id,url,times_,log_level))
            thread.start()
            threads.append(thread)
    if len(threads)!=0:
        for thread_ in threads:
            thread_.join()
    m,s=divmod(int(time.time()-start_time),60)
    h,m=divmod(m,60)
    logger.info("执行完成，选择内容可查看日志文件输出记录，用时 %02d:%02d:%02d 共提交 %d 份问卷。" %(h, m, s, times))