__author__ = 'Skuzzi'
import sys;
import re;
import datetime;
import paramiko;
import sqlalchemy;
import os.path;
import subprocess

"""Takes useless parameter x
    Verifies quantity of system arguments
    Returns 1 if all right; 0 if quantity is more or less than 4
"""
def verifyArgQuantity(x):
    x = len(sys.argv)
    if(x == 1):
        print('There is nothing left to found from ')
        return 0;
    if(x == 2):
        print('Please input period of time ')
        return 0;
    if(x == 3):
        print('Please input second bound of time ')
        return 0;
    if(x > 4):
        print('Too many arguments are given ')
        return 0;
    return 1

"""Gets string of cameras
Verifies it for matching correct format: camera1,[camera2,camera3...]
Returns string of cameras if all right;If no returns None
"""
def verifyCameras(inputString):#Verifies string:whether it matches input format or not
    cameras = re.match( r'^(([0-9]+)(,([0-9]+))*)$', inputString,).group()#First argument is string of cameras
    if(cameras):
        return cameras;
    else:
        return None;

"""Gets i-number of system argument and array of system arguments
Verifies it for matching correct format of data: "Year-month-day" (example:"2012-02-20"); if month or day has 1 digit,
    leading zero is neccessary
If all right returns date; if no returns None
"""
def verifyDate(i, sysArgv):#Verifies Date for matching date format;i=2-MinDate,i=3-MaxDate,other is not correct
    date = re.match(r'^([0-9]{4})-([0-1][0-9])-([0-3][0-9])$', sysArgv,);
    if date:
        yearLimit = int(date.group(1));
        monthLimit = int(date.group(2));
        dayLimit = int(date.group(3));
        return datetime.date(yearLimit,monthLimit,dayLimit);
    else:
        print('Incorrect date format')
        return None;

"""Gets list cameras
Searches directory for every camera
Returns list of directories if all right; if no returns None
"""
def sqlWorkingWith(cameras):#Function takes from database list of directories of cameras
        # Arg cameras is string consisting list of cameras
    import json
    from sqlalchemy import create_engine
    dirList = [];
    engine = sqlalchemy.create_engine('mysql+pymysql://root:vtntjhjkjubz@192.168.1.230/cup_system3') # connect to server
    connection = engine.connect()
    result = connection.execute("select id,properties from objects where id in(%s) AND type = 2"%cameras )
    for row in result:
        data  = json.loads(row.properties)
        dirList.append(data['dir'])
    connection.close()
    if(dirList):
        return dirList
    else:
        return None

"""Gets nothing
Verifies min and max Date
Returns None if something is wrong; Returns list of dates containing min and max date if all right
"""
def searchDate():
    x = len(sys.argv)
    if(verifyArgQuantity(x) == 0):
        print('Incorrect arguments. Verify your cameras,minDate and maxDate')
        return None
    minDate = verifyDate(2, sys.argv[2])#Send there i=2 to take min Date
    maxDate = verifyDate(3, sys.argv[3])#Send there i=2 to take max Date
    if(minDate == None or maxDate == None or minDate > maxDate):
        print('Incorrect arguments. Verify your minDate and maxDate')
        return None;
    dateList = []
    dateList.append(minDate)
    dateList.append(maxDate)
    date = minDate
    while(date < maxDate):
        date += datetime.timedelta(days = 1)
    return dateList;

"""Gets nothing
Searches directories for cameras
Returns list of directories if all right;Returns None if something is wrong
"""
def searchDir():
    cameras = verifyCameras(sys.argv[1]);
    if(cameras == None):
        print('Incorrect arguments. Verify your cameras,minDate and maxDate')
        return None
    dirList = sqlWorkingWith(cameras)
    return dirList

"""Gets list of directories for cameras and list of dates
Sets connecting with server and copies files from server
Returns 1 if all right
"""
def setConnecting(dirList, dateList):#Принимает список ОТНОСИТЕЛЬНЫХ адресов папок, мин. и макс. дату в виде одного списка
    minYear = dateList[0].year
    maxYear = dateList[1].year
    minMonth = dateList[0].month
    maxMonth = dateList[1].month
    minDay = dateList[0].day
    maxDay = dateList[1].day
    host = '192.168.1.233'
    user = 'root'
    secret = 'vtntjhjkjubz'
    port = 22
    transport = paramiko.Transport((host, port))
    transport.connect(username = user, password = secret)
    sftp = paramiko.SFTPClient.from_transport(transport)
    mainDir = "/var/archive/video_archive/"
    sftp.chdir(mainDir)
    photo = "/photo/"
    os.chdir('/')
    try:#Создаём папку, где будут все фотографии
        os.mkdir('photo')
        os.chdir('photo/')
    except OSError:
        os.chdir('photo/')
    for cameraDir in dirList:
        os.chdir(photo + "/")
        sftp.chdir(mainDir)
        directories = cameraDir.split('/')
        for directory in directories:
            try:#Создали в папке Фото папку текущей (обрабатываемой) камеры
                os.mkdir(directory)
                os.chdir(directory + "/")
            except OSError:
                os.chdir(directory + "/")
        sftp.chdir(mainDir + cameraDir)
        os.chdir(photo + cameraDir + "/")
        year = minYear
        while(year <= maxYear):
            if str(year) in sftp.listdir(mainDir + cameraDir + "/"):
                sftp.chdir(mainDir + cameraDir + "/" + str(year))
                os.chdir(photo + cameraDir + "/")
                try:#Создали в папке Фото папку текущего (обрабатываемого) года
                    os.mkdir(str(year))
                    os.chdir(str(year) + "/")
                except OSError:
                    os.chdir(str(year) + "/")
                sftp.chdir(mainDir + cameraDir + "/")
                minMonthCur = minMonth#Если год в промежутке, то надо начинать с 1 месяца
                if(year > minYear):
                    minMonthCur = 1;
                month = minMonthCur
                maxMonthCur = maxMonth
                if(year < maxYear):
                    maxMonthCur = 12;
                while(month <= maxMonthCur):
                    monthNormal = "0"
                    if(month < 10):
                        monthNormal = "0" + str(month)#Формат месяца:01,02...,10,11,12 -Приводим к формату вручную
                    else:
                        monthNormal = str(month)
                    if monthNormal in sftp.listdir(mainDir + cameraDir + "/" + str(year)):
                        sftp.chdir(mainDir + cameraDir + "/" + str(year) + "/" + monthNormal)
                        os.chdir(photo + cameraDir + "/" + str(year) + "/")
                        try:#Создали в папке Фото папку текущего (обрабатываемого) месяца
                            os.mkdir(monthNormal)
                            os.chdir(monthNormal + "/")
                        except OSError:
                            os.chdir(monthNormal + "/")
                        minDayCur = minDay
                        if(month > minMonthCur or (month==minMonthCur and year>minYear)):
                            minDayCur = 1;
                        day = minDayCur
                        maxDayCur = maxDay
                        if(month < maxMonthCur or (month==maxMonthCur and year<maxYear)):
                            maxDayCur = 31
                        while(day <= maxDayCur):
                            if(day < 10):
                                dayNormal = "0" + str(day)#Формат дня:01,02...,10,11,12... -Приводим к формату вручную
                            else:
                                dayNormal = str(day)
                            if dayNormal in sftp.listdir(mainDir + cameraDir + "/" + str(year) + "/" + monthNormal):
                                sftp.chdir(mainDir + cameraDir + "/" + str(year) + "/" + monthNormal + "/" + dayNormal)
                                os.chdir(photo + cameraDir + "/" + str(year) + "/" + monthNormal + "/")
                                try:#Создали в папке месяца папку текущего (обрабатываемого) дня
                                    os.mkdir(dayNormal)
                                    os.chdir(dayNormal + "/")
                                except OSError:
                                    os.chdir(dayNormal + "/")
                                for f in sftp.listdir(mainDir + cameraDir+"/"+str(year)+"/"+monthNormal+"/"+dayNormal):
                                    sftp.get(mainDir + cameraDir + "/"+str(year)+"/"+monthNormal+"/"+dayNormal+"/"+f,f)
                            day = day + 1
                    month = month + 1
            year = year + 1;
    sftp.close()
    transport.close()
    return 1

"""Gets nothing
Main function unites functions
Returns 1 if all right
"""
def main():
    dirList = searchDir()
    if(dirList==None):
        print("Cameras has not been found. ")
        return None
    dateList = searchDate()
    if(dirList==None or dateList==None):
        print("Incorrect date format found. ")
        return None
    setConnecting(dirList, dateList)
    try:#Создали в папке Фото папку текущего (обрабатываемого) месяца
        os.mkdir("/Your_Photo_Archive")
        os.chdir("/Your_Photo_Archive/"+ "/")
    except OSError:
        os.chdir("/Your_Photo_Archive/" + "/")
    subprocess.call("c:\\winrar a \"c:\\Your_Photo_Archive\\Your_Photo_Archive.rar\" \"c:\photo\"")
    return 1
main();
