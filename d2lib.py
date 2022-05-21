# -*- coding:utf-8 -*-

"""
    D2Lib
    by ArthurZhou
    https://github.com/ArthurZhou/D2Lib
"""

# These are built-in packages
import _thread
import configparser
import logging
import os.path
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# You need to install these extra packages
try:
    import markdown  # markdown
    import markdown.extensions
except ImportError:
    print('\033[0;51;91mFailed to load package: markdown. Have you installed it?\033[0m')
    sys.exit(0)

VER = '1.0.0'  # version

# check config file
if os.path.exists('d2lib.ini'):
    config = configparser.ConfigParser()
    config.read('d2lib.ini')
else:
    try:
        print('Please stand by while D2Lib{0} is preparing on its first launch.')
        wriConfig = open('d2lib.ini', 'w')
        wriConfig.write('[Path]\n'
                        '; home page in your directory(works for all sub dirs in your main folder)\n'
                        'home=Home.md\n'
                        '; 404 page(same as \'home\')\n'
                        '404page=404.md\n\n'
                        '[Network]\n'
                        'ip=0.0.0.0\n'
                        'port=80\n\n'
                        '; NAT allows you to open your site from outer Internet.\n'
                        '; In this version, we haven`t made a secure system. '
                        'So everyone got your link can look at your file!\n'
                        '; Learn more at: https://github.com/ArthurZhou/D2Lib/wiki/NAT\n'
                        'enable-nat=false\n\n'
                        '; enter your token from ngrok.net\n'
                        '; Get more information about how to get the token: '
                        'https://github.com/ArthurZhou/D2Lib/wiki/Get-token\n'
                        'nat-token=\n\n'
                        '[Misc]\n'
                        'log-to-file=false\n'
                        'markdown-css=true\n'
                        'txt-css=true\n')
        wriConfig.close()
        print('Config file saved to \'d2lib.ini\'.')
        print('Finished! Now restarting...')
        os.execl(sys.executable, sys.executable, *sys.argv)
    except PermissionError:
        print('\033[0;51;91mD2Lib failed to launch because it has no permission on creating files.')

# read config file
try:
    HOME = '/' + config.get('Path', 'home')  # home page
    FNF_PAGE = '/' + config.get('Path', '404page')  # 404 page
    IP = config.get('Network', 'ip')  # ip
    PORT = config.getint('Network', 'port')  # web page port(default 80)
    ENABLE_NAT = config.getboolean('Network', 'enable-nat')
    TOKEN = config.get('Network', 'nat-token')
    LOG_TO_FILE = config.getboolean('Misc', 'log-to-file')  # write logs to a file or not
    MARKDOWN_CSS = config.getboolean('Misc', 'markdown-css')  # use css style on markdown file or not(default True)
    TXT_CSS = config.getboolean('Misc', 'txt-css')  # use css style on plain text file or not(default True)
except KeyError and configparser.NoOptionError:
    if input('\033[0;51;91mInvalid config file! Do you want to restore it to default?\033[0m [Y/n]: ') == 'Y':
        os.remove('d2lib.ini')
        print('File removed! Restarting server...')
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        print('\033[0;51;91mD2Lib failed to launch because the config file is incorrect!\033[0m')
        sys.exit(0)

if ENABLE_NAT:
    try:
        from pyngrok import ngrok  # import api
        import pyngrok.exception

        print('You enabled nat proxy. This proxy is provided by \'ngrok\'. Using \'pyngrok\' as an API.\n'
              '\033[1;30;41mPlease follow the law of your country or region when you are using it!\n'
              'We take no responsibility for any problems caused by the programme!\n'
              'Continue means you AGREE with our License https://github.com/ArthurZhou/D2Lib/wiki/Bulit-in-NAT-LICENSE'
              '\033[0m')
        if input('ARE YOU SURE TO \033[4mCONTINUE AND ACCEPT\033[0m our license??? [Y/n]') == 'Y':  # ask if continue
            print('Trying to connecting to ngrok service...(if this is the first time you launch this, '
                  'it may take a few time to download the file)')
            try:
                ngrok.set_auth_token(TOKEN)
                http_tunnel = ngrok.connect(PORT, 'http')
            except pyngrok.exception.PyngrokNgrokHTTPError:
                pass
            print('Success!Tunnel information: ' + str(ngrok.get_tunnels()[0]))
            firstQuote = str(ngrok.get_tunnels()[0]).find('"') + 1
            domain = str(ngrok.get_tunnels()[0])[firstQuote:str(ngrok.get_tunnels()[0])
                                                            [firstQuote + 1:].find('"') + firstQuote + 1]
            print('Server outer domain: ' + domain)
        else:
            print('You don`t want to start the service or disagree with our license. You can disable this service '
                  'by editing d2lib.ini .')
            sys.exit(0)
    except ImportError:
        print('\033[0;51;91mYou enabled nat proxy. But you haven`t installed \'pyngrok\'!')
        sys.exit(0)

# set html template
CHUCK1 = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>'
CHUCK2 = '</title><style>body{background-color: #292929;}div{margin: 20px; padding: 10px;}hr{border-top: 5px ' \
         'solid#c3c3c3; border-bottom-width: 0; border-left-width: 0; border-right-width: 0; border-radius: 3px;}h1	' \
         '	{color: #c3c3c3; font-family: Arial; font-size: 250%; text-align: center; letter-spacing:3px;}h2		{' \
         'color: #c3c3c3; font-family: Arial; font-size: 220%; text-align: center; letter-spacing:3px;}h3		{' \
         'color: #c3c3c3; font-family: Arial; font-size: 190%; text-align: center; letter-spacing:3px;}h4		{' \
         'color: #c3c3c3; font-family: Arial; font-size: 170%; text-align: center; letter-spacing:3px;}h5	{color: ' \
         '#c3c3c3; font-family: Arial; font-size: 150%; text-align: center; letter-spacing:3px;}h6		{color: ' \
         '#c3c3c3; font-family: Arial; font-size: 130%; text-align: center; letter-spacing:3px;}code	{color: ' \
         '#c8c8c8; font-family: Courier New;}a		{text-decoration: None; color: #58748d; font-family: sans-serif; ' \
         'letter-spacing:0.7px;}a:link,a:visited		{color: #58748d;}a:hover	{color: #539899; text-decoration:' \
         ';}a:active	{color: #c3c3c3; background: #101010;}p		{color: #c3c3c3; font-family: Helvetica; ' \
         'font-size: 100%; display: inline; text-indent: 100px; letter-spacing:0.7px; line-height:120%;}ul		{' \
         'list-style-type: square; font-family: Helvetica; color: #c3c3c3;}ol		{font-family: Helvetica; color: ' \
         '#c3c3c3;}table	{border: 2px solid #101010; font-family: Helvetica;}th		{border: 0.5px solid #101010; ' \
         'font-family: Helvetica; color: #c3c0c3; font-weight: bold; text-align: center; padding: 10px;}td		{' \
         'font-family: Helvetica; color: #c3c3c3; text-align: center; padding: 2px;}#ul {list-style-type: none;margin:' \
         '0;padding: 0;overflow: hidden;background-color: #333;}#li {float: left;}#li a {display: block;color: ' \
         'white;text-align: center;padding: 14px 16px;text-decoration: none;}#li a:hover ' \
         '{background-color: #111;}</style></head><body><div><ul id="ul"> '
CHUCK3 = '</ul></div><div>'
CHUCK4 = '<br><br><hr><p>Powered by D2Lib</p></div></body></html>'
LIST_STYLE = '<li id="li"><a id="li" href="{0}">{1}</a></li>'

# get path
if getattr(sys, 'frozen', None):
    """
        !!! Although we made this, but we still don`t suggest you to packup this programme.
        Because it may cause a lot of nasty bugs.And we won`t get fix of your issue if you run it as a packed app!
        This is just a tip, running from packed app is ok according to our license.

        when you use pyinstaller to pack your library, just add ('file', '.') to the data option in the *.spec file
        this will pack the whole lib into the same directory of D2Lib.py.
        don`t worry, we`ve solved this problem
        when you are running a packed one, it will auto change the lib directory.
        but if you run from source code, you can put your file in a directory.
    """
    PATH = sys._MEIPASS  # run this when running a packed one
    LOG_FOLDER = PATH + '/log'
else:
    PATH = os.getcwd()  # run this when running from source
    LOG_FOLDER = PATH + '/log'
os.chdir(PATH + '/d2lib')

# add elements to title bar
content = LIST_STYLE.format(HOME, 'Home')
folderList = os.listdir()
for folders in folderList:
    if os.path.isdir(folders):
        content += LIST_STYLE.format('/' + folders + HOME, folders)
os.chdir(PATH)

if not os.path.exists(LOG_FOLDER) and LOG_TO_FILE:  # is log folder exist
    os.mkdir(LOG_FOLDER)

if not IP:  # if ip is blank, open server on localhost
    IP = '127.0.0.1'
if not PORT:  # if port is blank, open server on port 80
    PORT = 80


class HTTPHandler(BaseHTTPRequestHandler):
    """This is an HTTP request handler"""

    def do_GET(self, PATH=PATH):
        originPath = PATH + '/d2lib'
        PATH += '/d2lib'

        self.send_response(200)  # response
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        if os.path.exists(originPath + self.path) and self.path == '/favicon.ico':
            self.wfile.write(open(originPath + '/favicon.ico', 'rb').read())
        elif os.path.exists(PATH + urllib.parse.unquote(self.path)) and self.path != '/favicon.ico':  # is the url exist
            message = Reader.reader(PATH + self.path, PATH)
            self.wfile.write(bytes(message, "utf8"))
        else:  # file not found
            message = Reader.reader(FNF_PAGE, PATH)
            self.wfile.write(bytes(message, "utf8"))
            self.log_error('Error url: {0} .Redirected to 404 page.'.format(self.path))

    def log_message(self, text, *args):
        """This is a log handler. It moves logs to logging module`s handler"""
        logger.info(self.address_string() + str(args))


class Reader:
    @staticmethod
    def reader(path, PATH):
        def getInclude(path):
            readIO = open(urllib.parse.unquote(path), 'r')
            length = len(path)  # get file name length

            if path[length - 3:length] == '.md':  # if it`s a .md file
                if not MARKDOWN_CSS:
                    chuck22 = '</title></head><body><div><ul id="ul"> '
                else:
                    chuck22 = CHUCK2
                getText = readIO.read() + '\n'
                name = os.path.basename(urllib.parse.unquote(path))[:-3]
                if not MARKDOWN_CSS:
                    text = markdown.markdown(getText)
                else:
                    text = markdown.markdown(getText).replace('\n', '<br>')
                getText = CHUCK1 + name + chuck22 + content + CHUCK3 + text + CHUCK4
            elif path[length - 5:length] == '.html':  # if it`s a .html file
                getText = readIO.read() + '<div><br><br><hr><p>Powered by D2Lib</p></div>'
            else:  # if not
                try:  # try to open as a text file
                    if not TXT_CSS:
                        chuck22 = '</title></head><body><div><ul id="ul"> '
                    else:
                        chuck22 = CHUCK2
                    name = os.path.basename(urllib.parse.unquote(path))
                    text = '<p>' + readIO.read().replace('\n', '<br>') + '</p>'
                    getText = CHUCK1 + name + chuck22 + content + CHUCK3 + text + CHUCK4
                except Exception:  # if failed to open it
                    logger.warning('Cannot open file: {0}'.format(path))
                    getText = 'Failed to get file!'
            readIO.close()
            return getText

        getText = ''
        try:  # if file exists
            getText = getInclude(path)
        except FileNotFoundError:  # file not found
            getText = getInclude(PATH + FNF_PAGE)
        except IsADirectoryError:  # blank path
            getText = getInclude(PATH + HOME)
        except PermissionError:
            logger.error('Permission denied while opening {0}!'.format(path))
        except IOError:
            pass
        return getText


class Checker:
    """This is used to check files and folders"""

    def __init__(self):
        if os.path.exists(PATH) and os.path.exists(PATH + '/d2lib' + HOME) and \
                os.path.exists(PATH + '/d2lib' + FNF_PAGE):
            logger.info('Everything is on its way!Starting main progress...')
            try:
                Starter()  # everything alright,fire it up
            except KeyboardInterrupt:
                logger.info('Server stopped!')
                try:
                    ngrok.disconnect(domain)
                except Exception:
                    pass
                sys.exit(0)
        else:  # something lost
            logger.critical('Error:Path error!')
            sys.exit(0)


class Starter:
    @staticmethod
    def startHTTP():
        try:
            with ThreadingHTTPServer((IP, PORT), HTTPHandler) as httpServer:  # start server
                logger.info('Web server started on http://{0}:{1}'.format(IP, PORT))
                _thread.start_new_thread(ServerKit.command, (httpServer, ))
                httpServer.serve_forever()
        except Exception as e:
            logger.critical(e)

    def __init__(self):
        Starter.startHTTP()


class ServerKit:
    @staticmethod
    def command(httpServer):
        logger.info('ServerKit console - built-in command line tool 1.0.0 Type \'help\' to get help.')
        while True:
            inputCmd = input()
            if inputCmd == 'help':
                print('Type \'help\' to show this page. \'stop\' to stop the server, and \'restart\' to restart it.')
            elif inputCmd == 'stop':
                logger.info('Server shutting down...')
                httpServer.shutdown()
                sys.exit(0)
            elif inputCmd == 'restart':
                os.execl(sys.executable, sys.executable, *sys.argv)

    def __init__(self):
        global logger
        logger = logging.getLogger()
        logName = ('/' + time.ctime(time.time()) + '.log').replace(' ', '-')
        FORMAT = logging.Formatter('[{asctime}] ({levelname}|{name}): {message}', style='{')
        text_handler = logging.StreamHandler()
        logging.Handler.setFormatter(text_handler, FORMAT)
        logger.setLevel(logging.INFO)
        # Add the handler to logger
        logger.addHandler(text_handler)
        if LOG_TO_FILE:
            file_handler = logging.FileHandler(filename=LOG_FOLDER + logName, encoding='utf-8')
            logger.addHandler(file_handler)
        logger.info('ServerKit console version 1.0.0  Type \'stop\' or use Ctrl+C to stop it.')
        logger.info('D2Lib Server version:{0}.Lib path:{1}.Log-to-file statue:{2}'.format(VER, PATH,
                                                                                          str(LOG_TO_FILE)))
        Checker()


class RateCounter:
    """This is used to check if the thread is hanged up or not."""

    def __init__(self):
        while True:
            startTime = time.time()
            currentLoop = 0
            while currentLoop < 1:
                time.sleep(0.99)
                currentLoop += 1
            analyze = time.time() - startTime
            if analyze <= 1:
                pass
            else:
                skipTime = str(int(analyze / 3600)) + "h-" + str(int(analyze / 60) % 60) + "m-" + \
                           str(round(analyze % 60, 2)) + "s"
                logger.warning('Can`t keep up!Skip {0} ~= {1} seconds.'.format(analyze, skipTime))


_thread.start_new_thread(RateCounter, ())
startTime = time.time()
ServerKit()
