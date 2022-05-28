# -*- coding:utf-8 -*-

"""
    D2Lib
    by ArthurZhou
    https://github.com/ArthurZhou/D2Lib
"""

# These are built-in packages
import _thread
import configparser
import hashlib
import logging
import mimetypes
import os.path
import posixpath
import sys
import time
import urllib.parse
from flask import Flask, request, redirect, render_template, session, send_file
from multiprocessing import Process

# You need to install these extra packages
try:
    import markdown  # markdown
    import markdown.extensions
except ImportError:
    print('\033[0;51;91mFailed to load package: markdown. Have you installed it?\033[0m')
    sys.exit(0)

VER = '1.2.0-beta3'  # version


def resetConfig():
    try:
        print('Please stand by while D2Lib{0} is preparing on its first launch.'.format(VER))
        wriConfig = open('d2lib.ini', 'w')  # create config file
        wriConfig.write('[Path]\n'
                        '; home page in your directory(works for all sub dirs in your main folder)\n'
                        'home=Home.md\n'
                        '; 404 page(same as \'home\')\n'
                        '404page=404.md\n\n'
                        '[Network]\n'
                        'ip=0.0.0.0\n'
                        'port=80\n'
                        'enable-ftp=true\n'
                        'ftp-port=21\n'
                        'ftp-user=root\n'
                        'ftp-psw=root\n'
                        '; block requests that use ip as host\n'
                        'block-request-from-ip=false\n'
                        '; do not response while using ip as host(you don`t need to fill it if '
                        '\'block-request-from-ip\' is false)\n'
                        'block-ip-request-by-not-response=\n'
                        '; redirect to a page while using ip as host(you don`t need to fill it if '
                        '\'block-ip-request-by-not-response\' is true)\n'
                        'block-ip-redirect=\n\n'
                        '; NAT allows you to open your site from outer Internet.\n'
                        '; In this version, we haven`t made a secure system. '
                        'So everyone got your link can look at your file!\n'
                        '; Learn more at: https://github.com/ArthurZhou/D2Lib/wiki/NAT\n'
                        'enable-nat=false\n\n'
                        '; enter your token from ngrok.net\n'
                        '; Get more information about how to get the token: '
                        'https://github.com/ArthurZhou/D2Lib/wiki/Get-token\n'
                        'nat-token=\n\n'
                        '; If you enable https, http connection will be skipped!\n'
                        '; About how to setup certificate, visit: https://github.com/ArthurZhou/D2Lib/wiki/'
                        'Generate-server-SSL-Certificate-for-HTTPS-connections\n'
                        'enable-https=false\n\n'
                        '[Misc]\n'
                        'log-to-file=false\n'
                        'markdown-css=true\n'
                        'txt-css=true\n'
                        'show-menubar=true\n'
                        'enable-auth=true\n'
                        'enable-login-api=false\n')
        wriConfig.close()
        print('Config file saved to \'d2lib.ini\'.')
        print('Generating auth pool...')
        open('auth.key', 'w').close()  # create account pool
        print('Finished! Now restarting...')
        os.execl(sys.executable, sys.executable, *sys.argv)  # restart
    except PermissionError:  # no permission to write
        print('\033[0;51;91mD2Lib failed to launch because it has no permission on creating files.')


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

app = Flask(__name__)
app.secret_key = 'QWERTYUIOP'


def readConfig(noReloadNGROK=False):
    """This function read in and global configs"""
    global HOME, FNF_PAGE, IP, PORT, FTP_PORT, FTP_USER, FTP_PSW, ENABLE_FTP, ENABLE_NAT, BLOCK_REQUEST_FROM_IP, \
        BLOCK_IP_REQUEST_BY_NOT_RESPONSE, ENABLE_AUTH, BLOCK_IP_REDIRECT, ENABLE_HTTPS, LOG_TO_FILE, MARKDOWN_CSS, \
        TXT_CSS, SHOW_MENUBAR, ENABLE_LOGIN_API, content

    # check config file
    if os.path.exists('d2lib.ini') and os.path.exists('auth.key'):
        config = configparser.ConfigParser()
        config.read('d2lib.ini')
    else:
        resetConfig()
    LIST_STYLE = '<li class="menu"><a class="menu" href="{0}">{1}</a></li>'

    # read config file
    try:
        HOME = '/' + config.get('Path', 'home')  # home page
        FNF_PAGE = '/' + config.get('Path', '404page')  # 404 page
        IP = config.get('Network', 'ip')  # ip
        PORT = config.getint('Network', 'port')  # web page port(default 80)
        ENABLE_FTP = config.getboolean('Network', 'enable-ftp')
        BLOCK_REQUEST_FROM_IP = config.getboolean('Network', 'block-request-from-ip')
        ENABLE_NAT = config.getboolean('Network', 'enable-nat')
        TOKEN = config.get('Network', 'nat-token')
        ENABLE_HTTPS = config.getboolean('Network', 'enable-https')
        LOG_TO_FILE = config.getboolean('Misc', 'log-to-file')  # write logs to a file or not
        MARKDOWN_CSS = config.getboolean('Misc', 'markdown-css')  # use css style on markdown file or not(default True)
        TXT_CSS = config.getboolean('Misc', 'txt-css')  # use css style on plain text file or not(default True)
        SHOW_MENUBAR = config.getboolean('Misc', 'show-menubar')  # show menubar or not
        ENABLE_AUTH = config.getboolean('Misc', 'enable-auth')
        ENABLE_LOGIN_API = config.getboolean('Misc', 'enable-login-api')
    except KeyError and configparser.NoOptionError:
        if input('\033[0;51;91mInvalid config file! Do you want to restore it to default?\033[0m [Y/n]: ') == 'Y':
            os.remove('d2lib.ini')
            print('File removed! Restarting server...')
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            print('\033[0;51;91mD2Lib failed to launch because the config file is incorrect!\033[0m')
            sys.exit(0)

    if ENABLE_FTP:
        global servers, DummyAuthorizer, FTPHandler
        from pyftpdlib import servers
        from pyftpdlib.authorizers import DummyAuthorizer
        from pyftpdlib.handlers import DummyAuthorizer
        FTP_PORT = config.getint('Network', 'ftp-port')
        FTP_USER = config.get('Network', 'ftp-user')
        FTP_PSW = config.get('Network', 'ftp-psw')

    # special settings
    if BLOCK_REQUEST_FROM_IP:  # block requests which use ip as host
        BLOCK_IP_REQUEST_BY_NOT_RESPONSE = config.getboolean('Network', 'block-ip-request-by-not-response')
        if not BLOCK_IP_REQUEST_BY_NOT_RESPONSE:
            BLOCK_IP_REDIRECT = '/' + config.get('Network', 'block-ip-redirect')

    if ENABLE_NAT and not noReloadNGROK:  # enable NAT connection and start a tunnel
        try:
            from pyngrok import ngrok  # import api
            import pyngrok.exception
            global pyngrok, ngrok, http_tunnel, domain

            # show warning about NAT service License
            print('You enabled NAT. This service is provided by \'ngrok\'. Using \'pyngrok\' as an API.\n'
                  '\033[1;30;41mPlease follow the law of your country or region when you are using it!\n'
                  'We take no responsibility for any problems caused by the programme!\n'
                  'Continue means you AGREE with our License '
                  'https://github.com/ArthurZhou/D2Lib/wiki/Bulit-in-NAT-LICENSE!\033[0m')
            if input(
                    'ARE YOU SURE TO \033[4mCONTINUE AND ACCEPT\033[0m our license??? [Y/n]') == 'Y':  # continue?
                print('Trying to connecting to ngrok service...(if this is the first time you launch this, '
                      'it may take a few time to download the file)')
                try:
                    if TOKEN:  # is field 'token' filled
                        ngrok.set_auth_token(TOKEN)  # set login token
                        http_tunnel = ngrok.connect(PORT, 'http')  # start tunnel
                    else:
                        print('\033[0;51;91mYou haven`t set a token for ngrok!\033[0m')
                        sys.exit(0)
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

    # add elements to title bar
    if SHOW_MENUBAR:
        os.chdir(PATH + '/d2lib')
        content = LIST_STYLE.format(HOME, 'Home')
        folderList = os.listdir()
        for folders in folderList:
            if os.path.isdir(folders) and folders[0:2] != '!$':
                content += LIST_STYLE.format('/' + folders + HOME, folders)
        os.chdir(PATH)
    else:
        content = ''
        os.chdir(PATH)

    if not os.path.exists(LOG_FOLDER) and LOG_TO_FILE:  # is log folder exist
        os.mkdir(LOG_FOLDER)

    if not IP:  # if ip is blank, open server on localhost
        IP = '127.0.0.1'
    if not PORT:  # if port is blank, open server on port 80
        PORT = 80


readConfig()


@app.route('/login', methods=['GET', "POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    user = request.form.get('user')
    psw = request.form.get('psw')
    if hashlib.sha256((user + ':' + psw).encode('utf-8')).hexdigest() in keyList:
        session['user'] = user
        return redirect('/')
    else:
        return render_template('login.html', msg='Error username or password')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    user_info = session.get('user')
    if not user_info:
        return redirect('/login')
    if os.path.exists(PATH + '/d2lib/' + path) and path == '/favicon.ico':  # get icon
        return open(PATH + '/d2lib/favicon.ico', 'rb').read()
    elif os.path.exists(
            PATH + '/d2lib/' + urllib.parse.unquote(path)) and path != '/favicon.ico':  # is the url exist
        name, text = Reader.reader(PATH + '/d2lib/' + path, PATH)
        if not name:
            return send_file(PATH + '/d2lib/' + urllib.parse.unquote(path), mimetype=text)
        else:
            return render_template('index.html', name=name, text=text, content=content)
    else:  # file not found
        name, text = Reader.reader(PATH + '/d2lib' + FNF_PAGE, PATH)
        logger.error('Error url: {0} .Redirected to 404 page.'.format(path))
        return render_template('index.html', name=name, text=text, content=content)


@app.route('/logout')
def logout():
    del session['user']
    return redirect('login')


class Reader:
    @staticmethod
    def reader(path, PATH):
        def getInclude(path):
            readIO = open(urllib.parse.unquote(path), 'r')
            length = len(path)  # get file name length

            if path[length - 3:length] == '.md':  # if it`s a .md file
                getText = readIO.read() + '\n'
                name = os.path.basename(urllib.parse.unquote(path))[:-3]
                getText = markdown.markdown(getText.replace('\n\n', '<br>\n\n'),
                                            extensions=['markdown.extensions.fenced_code',
                                                        'markdown.extensions.tables', 'markdown_checklist.extension'])
            elif path[length - 5:length] == '.html':  # if it`s a .html file
                """
                getText = readIO.read().replace('<d2libstyle />', '<style>' + CSS + '</style') \
                          .replace('<d2libcontent />', '<div><ul id="ul">' + content + '</ul></div>') \
                          .replace('<d2libtext>', '<div id="div">') \
                          .replace('</d2libtext>', '</div>') \
                          + '<div><br><br><hr><p>Powered by D2Lib</p></div>'
                """
                pass
            elif path[length - 4:length] == '.txt':  # if it`s a .txt file
                name = os.path.basename(urllib.parse.unquote(path))
                getText = '<p>' + readIO.read().replace('\n', '<br>') + '</p>'
            else:  # if none of the above
                name = False
                base, ext = posixpath.splitext(path)
                if ext in extensions_map:
                    getText = extensions_map[ext]
                elif ext.lower() in extensions_map:
                    getText = extensions_map[ext]
                else:
                    getText = extensions_map['']

            readIO.close()
            return name, getText

        name = ''
        getText = ''
        try:  # if file exists
            name, getText = getInclude(path)
        except FileNotFoundError:  # file not found
            name, getText = getInclude(PATH + '/d2lib' + FNF_PAGE)
        except IsADirectoryError:  # blank path
            name, getText = getInclude(PATH + '/d2lib' + HOME)
        except PermissionError:
            logger.error('Permission denied while opening {0}!'.format(path))
        except IOError:
            pass
        return name, getText


class Checker:
    """This is used to check files and folders"""

    def __init__(self):
        if os.path.exists(PATH) and os.path.exists(PATH + '/d2lib' + HOME) and \
                os.path.exists(PATH + '/d2lib' + FNF_PAGE):
            if ENABLE_HTTPS and os.path.exists(PATH + 'key.pem') and os.path.exists(PATH + 'cert.pem'):
                logger.critical('You enabled https, but \'cert.pem\' and \'key.pem\' don`t exist! ')
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
    def accountLoader():
        global keyList
        keyList = []
        logger.info('Loading accounts...')
        authFile = open('auth.key', 'r')
        keys = authFile.read().split('\n')
        num = 0

        for lines in keys:  # load accounts line by line
            if not lines:
                break
            keyList.append(lines)
            num += 1
        logger.info('Loaded {0} account(s).'.format(num))
        if num == 0:
            logger.warning('There`s no active account!You can add one by typing \'account add <username> <password>\'.')
        elif not keys[num]:  # if the last element is blank, delete it(cause by the blank line at the end of file)
            del keys[num]

        authFile.close()

    @staticmethod
    def startHTTP():
        global server
        Starter.accountLoader()
        try:
            try:
                if ENABLE_HTTPS:
                    app.run(host=IP, port=PORT, ssl_context=('cert.pem', 'key.pem'), debug=False)
                else:
                    app.run(host=IP, port=PORT, debug=False)
            except BrokenPipeError:
                logger.info('Connection lost.')
        except Exception as e:
            logger.critical(e)
            logger.exception(repr(e))

    @staticmethod
    def startFTP():
        global ftpServer
        authorizer = DummyAuthorizer()
        authorizer.add_user(FTP_USER, FTP_PSW, '.', perm='elradfmwMT')
        handler = FTPHandler
        handler.authorizer = authorizer
        ftpServer = servers.FTPServer((IP, FTP_PORT), handler)
        logger.info('Ftp server started on ftp://{0}:{1}.'.format(IP, FTP_PORT))
        ftpServer.serve_forever()

    def __init__(self):
        try:
            _thread.start_new_thread(ServerKit.command, ())  # start command line tool
            if ENABLE_FTP:
                _thread.start_new_thread(Starter.startFTP, ())
            Starter.startHTTP()
        except KeyboardInterrupt:
            sys.exit(0)


class ServerKit:
    @staticmethod
    def command():
        def restartNgrok():
            global domain, http_tunnel
            logger.info('Restarting ngrok...')
            ngrok.disconnect(domain)
            del globals()['domain']
            try:
                http_tunnel = ngrok.connect(PORT, 'http')
            except pyngrok.exception.PyngrokNgrokHTTPError:
                pass
            logger.info('Success!Tunnel information: ' + str(ngrok.get_tunnels()[0]))
            firstQuote = str(ngrok.get_tunnels()[0]).find('"') + 1
            domain = str(ngrok.get_tunnels()[0])[firstQuote:str(ngrok.get_tunnels()[0])
                                                 [firstQuote + 1:].find('"') + firstQuote + 1]
            logger.info('Server outer domain: ' + domain)

        def reloadConfig():
            if os.path.exists('d2lib.ini'):
                if not BLOCK_REQUEST_FROM_IP:
                    globVarList = ['HOME', 'FNF_PAGE', 'IP', 'PORT', 'LOG_TO_FILE', 'MARKDOWN_CSS', 'TXT_CSS',
                                   'ENABLE_AUTH', 'ENABLE_HTTPS', 'SHOW_MENUBAR', 'CHUCK1', 'CHUCK2', 'CHUCK3',
                                   'CHUCK4', 'content']
                elif BLOCK_IP_REQUEST_BY_NOT_RESPONSE:
                    globVarList = ['HOME', 'FNF_PAGE', 'IP', 'PORT', 'LOG_TO_FILE', 'MARKDOWN_CSS', 'TXT_CSS',
                                   'ENABLE_AUTH', 'ENABLE_HTTPS', 'SHOW_MENUBAR', 'CHUCK1', 'CHUCK2', 'CHUCK3',
                                   'CHUCK4', 'content', 'BLOCK_REQUEST_FROM_IP', 'BLOCK_IP_REQUEST_BY_NOT_RESPONSE']
                else:
                    globVarList = ['HOME', 'FNF_PAGE', 'IP', 'PORT', 'LOG_TO_FILE', 'MARKDOWN_CSS', 'TXT_CSS',
                                   'ENABLE_AUTH', 'ENABLE_HTTPS', 'SHOW_MENUBAR', 'CHUCK1', 'CHUCK2', 'CHUCK3',
                                   'CHUCK4', 'content', 'BLOCK_REQUEST_FROM_IP', 'BLOCK_IP_REQUEST_BY_NOT_RESPONSE',
                                   'BLOCK_IP_REDIRECT']
                for globVars in globVarList:
                    del globals()[globVars]  # delete values
                readConfig(True)
            else:
                resetConfig()

        logger.info('ServerKit console - built-in command line tool 1.0.0 Type \'help\' to get help.')
        while True:
            inputCmd = input().split(' ')
            if inputCmd == 'help':
                print('Type \'help\' to show this page.\n'
                      'reload - only reload options(sometimes only reload options may not work)\n'
                      'account add <username> <password> - add an account\n')
            elif inputCmd[0] == 'reload':
                logger.info('Reloading configurations...')
                reloadConfig()
            elif inputCmd[0] == 'account' and len(inputCmd) == 4:
                if inputCmd[1] == 'add':
                    keyList.append(hashlib.sha256((inputCmd[2] + ':' + inputCmd[3]).encode('utf-8')).hexdigest())
                    authFile = open('auth.key', 'a')
                    authFile.write(hashlib.sha256((inputCmd[2] + ':' + inputCmd[3]).encode('utf-8')).hexdigest() + '\n')
                    authFile.close()
                    logger.info('Add new account: ' + inputCmd[2] + ' ' + inputCmd[3])
                elif inputCmd[1] == 'del':
                    keyList.remove(hashlib.sha256((inputCmd[2] + ':' + inputCmd[3]).encode('utf-8')).hexdigest())
                    authFile = open('auth.key', 'r')
                    keys = authFile.read().split('\n')
                    keys.remove(hashlib.sha256((inputCmd[2] + ':' + inputCmd[3]).encode('utf-8')).hexdigest())
                    authFile.close()
                    authFile = open('auth.key', 'w')
                    authFile.write('\n'.join(keys))
                    authFile.close()
                    logger.info('Delete account: ' + inputCmd[2] + ' ' + inputCmd[3])

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
        logger.info('ServerKit console version 1.1.0  Use Ctrl+C to stop it.')
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
if not mimetypes.inited:
    mimetypes.init()  # try to read system mime.types
extensions_map = mimetypes.types_map.copy()
extensions_map.update({
    '': 'application/octet-stream',  # Default
    '.py': 'text/plain',
    '.c': 'text/plain',
    '.h': 'text/plain',
})
ServerKit()
