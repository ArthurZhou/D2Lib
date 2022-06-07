# -*- coding:utf-8 -*-

"""
    D2Lib
    by ArthurZhou
    https://github.com/ArthurZhou/D2Lib

File structure:
<your folder>
    / D2Lib.py
    / d2lib
        / d2lib (file folder)
            / <your files to show>
        / templates (page templates)
            / index.html
            / login.html
        / auth.key (accounts)
        / d2lib.ini (configures)
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

# You need to install these extra packages
try:
    import markdown  # markdown
    import markdown.extensions
    import markdown_checklist.extension
except ImportError:
    print('\033[0;51;91mFailed to load package: markdown, markdown_checklist. Have you installed it?\033[0m')
    sys.exit(0)

VER = '1.2.0-stable'  # version


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
                        'enable-ftp=false\n'
                        'ftp-port=21\n'
                        'ftp-user=root\n'
                        'ftp-psw=root\n'
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
                        'enable-auth=true\n'
                        'show-menubar=true\n')
        wriConfig.close()
        print('Config file saved to \'d2lib.ini\'.')
        print('Generating auth pool...')
        open('auth.key', 'w').close()  # create account pool
        print('Finished! Restart is required.')
        sys.exit(0)
    except PermissionError:  # no permission to write
        print('\033[0;51;91mD2Lib failed to launch because it has no permission on creating files.')


if not os.path.exists('d2lib'):     # is folder 'd2lib' exist?
    os.mkdir('d2lib')
    os.mkdir('d2lib/d2lib')
    open('d2lib/d2lib/put_your_files_here', 'w').close()
os.chdir('d2lib')
PATH = os.getcwd()
LOG_FOLDER = PATH + '/log'

app = Flask(__name__, template_folder=PATH + '/templates')
app.secret_key = 'QWERTYUIOP'


def readConfig(noReloadNGROK=False):
    """This function read in and global configs"""
    global HOME, FNF_PAGE, IP, PORT, FTP_PORT, FTP_USER, FTP_PSW, ENABLE_FTP, ENABLE_NAT, ENABLE_AUTH, ENABLE_HTTPS, \
        LOG_TO_FILE, content

    # check config file
    print(os.getcwd())
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
        ENABLE_NAT = config.getboolean('Network', 'enable-nat')
        TOKEN = config.get('Network', 'nat-token')
        ENABLE_HTTPS = config.getboolean('Network', 'enable-https')
        LOG_TO_FILE = config.getboolean('Misc', 'log-to-file')  # write logs to a file or not
        SHOW_MENUBAR = config.getboolean('Misc', 'show-menubar')  # show menubar or not
        ENABLE_AUTH = config.getboolean('Misc', 'enable-auth')
    except KeyError and configparser.NoOptionError as e:
        print(repr(e))
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
        from pyftpdlib.handlers import FTPHandler
        FTP_PORT = config.getint('Network', 'ftp-port')
        FTP_USER = config.get('Network', 'ftp-user')
        FTP_PSW = config.get('Network', 'ftp-psw')

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
        if ENABLE_AUTH:
            content += '<li class="logout"><a class="logout" href="/logout">Log out</a></li>'
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
def login():    # login page handler
    if ENABLE_AUTH:     # check if auth in enabled
        if request.method == 'GET':     # if requester want to get page view(get page use 'GET' method,
            # while login form use 'POST' method)
            if request.args.get('login'):   # if use arguments to login (how to use this api to login:
                # https://github.com/ArthurZhou/D2Lib/blob/main/new_api.py)
                if hashlib.sha256((request.args.get('login')).encode('utf-8')).hexdigest() in keyList:
                    session['user'] = request.args.get('login').split(':')[0]
                    return redirect('/')
                else:
                    return render_template('login.html')
            else:
                return render_template('login.html')
        user = request.form.get('user')
        psw = request.form.get('psw')
        if hashlib.sha256((user + ':' + psw).encode('utf-8')).hexdigest() in keyList:
            session['user'] = user
            return redirect('/')    # success, redirect to home page
        else:
            return render_template('login.html', msg='Error username or password')  # error usr or psw
    else:
        return redirect('/')    # if auth is off, redirect to home page


@app.route('/logout')
def logout():   # logout page handler
    if ENABLE_AUTH:     # check if auth in enabled
        try:
            del session['user']     # delete login history in this session
        except KeyError:
            pass
        return redirect('login')    # after logout, go to login page
    else:
        return redirect('/')    # if auth is off, redirect to home page


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):    # file request handler
    user_info = session.get('user')
    if not user_info and ENABLE_AUTH:   # is the user logged in
        return redirect('/login')   # redirect to login page if not logged in
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
                fileInclude = readIO.read()
                name = fileInclude[fileInclude.find('<title>') + 7:fileInclude.find('</title>')]
                getText = fileInclude[fileInclude.find('<body>') + 6:fileInclude.find('</body>')]
            elif path[length - 4:length] == '.txt':  # if it`s a .txt file
                name = os.path.basename(urllib.parse.unquote(path))
                getText = '<p>' + readIO.read().replace('\n', '<br>') + '</p>'
            else:  # if none of the above
                name = False
                base, ext = posixpath.splitext(path)
                if ext in fileType:
                    getText = fileType[ext]
                elif ext.lower() in fileType:
                    getText = fileType[ext]
                else:
                    getText = fileType['']

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
            if not os.path.exists('templates') or not os.path.exists('templates/index.html') \
                    or not os.path.exists('templates/login.html'):
                os.mkdir('templates')
                open('templates/index.html', 'w').write('<!DOCTYPE html> <html lang="en"> <head>     <meta  '
                                                        'charset="UTF-8">     <title>{{name}}</title>     <style>      '
                                                        '  body{background-color:#292929;}        @keyframes '
                                                        'fadeInAnimation  {0% {opacity:0;} 100% {opacity:1;}}        '
                                                        'div {margin: 20px; padding: 10px;}        hr  {border-top: '
                                                        '5px solid#c3c3c3; border-bottom-width: 0; border-left-width: '
                                                        '0; border-right-width: 0; border-radius: 3px;}        h1  {'
                                                        'color: #c3c3c3; font-family: Arial,serif; font-size: 250%; '
                                                        'text-align: center; letter-spacing:3px;}        h2  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 220%; '
                                                        'text-align: center; letter-spacing:3px;}        h3  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 190%; '
                                                        'text-align: center; letter-spacing:3px;}        h4  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 170%; '
                                                        'text-align: center; letter-spacing:3px;}        h5  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 150%; '
                                                        'text-align: center; letter-spacing:3px;}        h6  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 130%; '
                                                        'text-align: center; letter-spacing:3px;}        code{color: '
                                                        '#c8c8c8; font-family: Courier New,serif;}        a   {'
                                                        'text-decoration: None; color: #58748d; font-family: '
                                                        'sans-serif; letter-spacing:1px;}a:link,        a:visited   {'
                                                        'color: #58748d;}        a:hover     {color: #539899; '
                                                        'text-decoration:none;}        a:active	{color: #c3c3c3; '
                                                        'background: #101010;}        p   {color: #c3c3c3; '
                                                        'font-family: Helvetica,serif;font-size: 100%; display: '
                                                        'inline; text-indent: 100px; letter-spacing:1px; '
                                                        'line-height:120%;}        p.warn      {color: #e33a3a; '
                                                        'font-family: Helvetica,serif;font-size: 100%; display: '
                                                        'inline; text-indent: 100px; letter-spacing:1px; '
                                                        'line-height:120%;}        ul  {list-style-type: square; '
                                                        'font-family: Helvetica,serif; color: #c3c3c3;}ol{font-family: '
                                                        'Helvetica,serif; color: #c3c3c3;}        table       {border: '
                                                        '2px solid #101010; font-family: Helvetica,serif;}        th  '
                                                        '{border: 1px solid #101010; font-family: Helvetica,'
                                                        'serif; color: #c3c0c3; font-weight: bold; text-align: center; '
                                                        'padding: 10px;}        td  {font-family: Helvetica,'
                                                        'serif; color: #c3c3c3; text-align: center; padding: 2px;}     '
                                                        '   input       {color: #c3c3c3; font-family: Helvetica,'
                                                        'serif; background: #101010; border-top-width: 0; '
                                                        'border-bottom-width: 0; border-left-width: 0; '
                                                        'border-right-width: 0; height: 20px; width: 200px;}        '
                                                        'div.fade    {animation: fadeInAnimation ease 0.3s; '
                                                        'animation-iteration-count: 1;animation-fill-mode: '
                                                        'forwards;}		ul.menu     {list-style-type: '
                                                        'none;margin:0;padding: 0;overflow: hidden;background-color: '
                                                        '#333;}		li.menu     {float: left;}        li.logout   {'
                                                        'float: right;}		li.menu a   {display: block;color: '
                                                        'white;text-align: center;padding: 14px 16px; text-decoration: '
                                                        'none;}		li.menu a:hover     {background-color: #111;}      '
                                                        '  li.logout a {display: block;color: #958a4b;text-align: '
                                                        'center;padding: 14px 16px; text-decoration: none;}		'
                                                        'li.logout a:hover   {background-color: #111;}    </style> '
                                                        '</head> <body>    <div><ul class="menu">{{'
                                                        'content|safe}}</ul></div>    <div class="fade">        {{'
                                                        'text|safe}}    </div>    <div><br><hr><p>Powered by '
                                                        'D2Lib</p></div> </body> </html>')
                open('templates/login.html', 'w').write('<!DOCTYPE html> <html lang="en"> <head>     <meta  '
                                                        'charset="UTF-8">     <title>Login</title>     <style>        '
                                                        'body{background-color:#292929;}        @keyframes '
                                                        'fadeInAnimation  {0% {opacity:0;} 100% {opacity:1;}}        '
                                                        'div {margin: 20px; padding: 10px;}        hr  {border-top: '
                                                        '5px solid#c3c3c3; border-bottom-width: 0; border-left-width: '
                                                        '0; border-right-width: 0; border-radius: 3px;}        h1  {'
                                                        'color: #c3c3c3; font-family: Arial,serif; font-size: 250%; '
                                                        'text-align: center; letter-spacing:3px;}        h2  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 220%; '
                                                        'text-align: center; letter-spacing:3px;}        h3  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 190%; '
                                                        'text-align: center; letter-spacing:3px;}        h4  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 170%; '
                                                        'text-align: center; letter-spacing:3px;}        h5  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 150%; '
                                                        'text-align: center; letter-spacing:3px;}        h6  {color: '
                                                        '#c3c3c3; font-family: Arial,serif; font-size: 130%; '
                                                        'text-align: center; letter-spacing:3px;}        code{color: '
                                                        '#c8c8c8; font-family: Courier New,serif;}        a   {'
                                                        'text-decoration: None; color: #58748d; font-family: '
                                                        'sans-serif; letter-spacing:1px;}a:link,        a:visited   {'
                                                        'color: #58748d;}        a:hover     {color: #539899; '
                                                        'text-decoration:none;}        a:active	{color: #c3c3c3; '
                                                        'background: #101010;}        p   {color: #c3c3c3; '
                                                        'font-family: Helvetica,serif;font-size: 100%; display: '
                                                        'inline; text-indent: 100px; letter-spacing:1px; '
                                                        'line-height:120%;}        p.warn      {color: #e33a3a; '
                                                        'font-family: Helvetica,serif;font-size: 100%; display: '
                                                        'inline; text-indent: 100px; letter-spacing:1px; '
                                                        'line-height:120%;}        ul  {list-style-type: square; '
                                                        'font-family: Helvetica,serif; color: #c3c3c3;}ol{'
                                                        'font-family: Helvetica,serif; color: #c3c3c3;}        table  '
                                                        '     {border: 2px solid #101010; font-family: Helvetica,'
                                                        'serif;}        th  {border: 1px solid #101010; font-family: '
                                                        'Helvetica,serif; color: #c3c0c3; font-weight: bold; '
                                                        'text-align: center; padding: 10px;}        td  {font-family: '
                                                        'Helvetica,serif; color: #c3c3c3; text-align: center; '
                                                        'padding: 2px;}        input       {color: #c3c3c3; '
                                                        'font-family: Courier,serif; background: #101010; '
                                                        'border-top-width: 0; border-bottom-width: 2px; '
                                                        'border-left-width: 0; border-right-width: 0; height: 30px; '
                                                        'width: 500px; font-size: 15px;}        div.fade    {'
                                                        'animation: fadeInAnimation ease 0.3s; '
                                                        'animation-iteration-count: 1;animation-fill-mode: forwards;} '
                                                        '   </style> </head> <body> {% if msg %}    <div> {% else %}  '
                                                        '  <div class="fade"> {% endif %}         <h1>Login to access '
                                                        'this site</h1>         <p>No idea about username and '
                                                        'password? Go and ask your service provider.</p><br>         '
                                                        '<a href="/">I think I`ve already logged in -></a>         '
                                                        '<hr>         <center>             <form  method="post">      '
                                                        '          <label>                <input type="text"  '
                                                        'name="user" >                </label><br>                '
                                                        '<label>                <input  type="password" name="psw" >  '
                                                        '              </label><br>                <input  '
                                                        'type="submit" name="Login"><br><br>                <p '
                                                        'class="warn">{{msg}}</p>             </form>         '
                                                        '</center>         <br><p>Powered by D2Lib</p>     </div> '
                                                        '</body> </html>')
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
            cli = sys.modules['flask.cli']
            cli.show_server_banner = lambda *x: None
            try:
                print(os.getcwd())
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

        logger.info('ServerKit console - built-in command line tool 1.3.0 Type \'help\' to get help.')
        while True:
            inputCmd = input().split(' ')
            if inputCmd == 'help':
                print('Type \'help\' to show this page.\n'
                      'account add <username> <password> - add an account\n'
                      'account del <username> <password> - delete an account\n')
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
if not mimetypes.inited:
    mimetypes.init()  # try to read system mime.types
fileType = mimetypes.types_map.copy()
fileType.update({
    '': 'application/octet-stream',  # Default
    '.py': 'text/plain',
    '.c': 'text/plain',
    '.h': 'text/plain',
})
ServerKit()
