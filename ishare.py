#! /usr/bin/python
# -*- coding:utf-8 -*-
from Tkinter import *
import tkFileDialog
import tkMessageBox
import cPickle
import re
import time
import webbrowser
import urllib
import urllib2
import httplib
import cookielib
import thread
import math
import tkFont
class AppWin(Frame):
    def __init__(self,master=None):
        Frame.__init__(self,master)
        self.root=self.winfo_toplevel()
        self.root.title("ishare downloader")
        #self.root.geometry('400x400+200+100')
        #self.root.pack_propagate(0)

        self.pack(side='top',fill='x',expand=1)

        #MODE=Frame(self,bg='#abcdef',bd=1)
        #MODE.pack(side='top',fill='x',expand=1)

        #mode=StringVar()
        #Radiobutton(MODE,variable=mode,text='view1',value='m1',command=self.mode1).pack(side='left',fill='x',expand=1)
        #Radiobutton(MODE,variable=mode,text='view2',value='m2',command=lambda:'expression').pack(side='left',fill='x',expand=1)

        self.PARAM=Frame(self,bg='#E1ECDD',bd=1)
        self.PARAM.pack(side='top',fill='x',expand=1)

        self.UINFO=Frame(self,bg='#eeeeee',bd=1)
        self.UINFO.pack(side='top',fill='x',expand=1)
        
        self.FLIST=Frame(self,bg='#ABCDEF',bd=1)
        self.FLIST.pack(side='top',fill='both',expand=1,anchor=W)

        self.FILTER=Frame(self)
        self.FILTER.pack(side='top',fill='x',expand=1)

        self.SELINFO=Frame(self)
        self.SELINFO.pack(side='top',fill='x',expand=1)

        self.INDEX=Frame(self,bg='#BCDEFA',bd=1)
        self.INDEX.pack(side='top',fill='both',expand=1)

        self.STATUS=Label(self,bg='#fff0d0',font=('system',8),bd=1)
        self.STATUS.pack(side='top',fill='both',expand=1)
        self.version=1.1
        self._FS_GRADE,self._FS_SELED,self._FS_UNSEL=2,1,0
        self.initData()
        self.mode1()
    def initData(self):
        self.filelist,self.searchlist,self.search=[],[],False
        self.pgCap,self.pgNo=20,0
    def getViewList(self):
        if(self.search): return self.searchlist
        else:return self.filelist
    def tdlFile(self,id):
        dlfn=self.filelist[id][1]
        dlurl=self.filelist[id][0].decode('cp936').encode('utf_8')
        self.STATUS['text']="downloading "+dlfn.decode('cp936').encode('utf_8')
        fid=re.search('(\d+?)\.html',dlurl).group(1)
        req=urllib2.Request('http://ishare.iask.sina.com.cn/download.php?fileid=%s'%(fid),"")
        req.add_header('Referer',dlurl)
        fd=urllib2.urlopen(req)
        block=10
        size=int(fd.info()['Content-Length'])
        bsize=size//(block-1)
        fs=open(dlfn,'wb')
        for i in range(1,block+1):
            if i==block:
                fs.write(fd.read(size%(block-1)))
            else:
                fs.write(fd.read(bsize))
            self.STATUS['text']="%d%%"%(i*10)
        fs.flush()
        fs.close()
        fd.close()
    def getDlink(self,finfo,new_referer):
        fn,dlurl=finfo[1],finfo[0].decode('cp936').encode('utf_8')
        fid=re.search('(\d+?)\.html',dlurl).group(1)
        ####no proxy supported
        #headers={
        #   "Content-type": "application/x-www-form-urlencoded",
        #   "Accept": "text/plain",
        #   "Accept-Encoding":"gzip, deflate",
        #   "Referer":dlurl,
        #   "Content-Length":"0"
        #   }
        #conn=httplib.HTTPConnection("ishare.iask.sina.com.cn")
        #conn.request("POST","/download.php?fileid=%s"%(fid),[],headers)
        #resp = conn.getresponse()
        #return resp.getheader('Location')
        ####auto support proxy
        redirect_handler = urllib2.HTTPRedirectHandler()
        #disable redirection request
        def no_redirect(req, fp, code, msg, hdrs, newurl): return None
        redirect_handler.redirect_request=no_redirect
        opener = urllib2.build_opener(redirect_handler)
        urllib2.install_opener(opener)
        req=urllib2.Request('http://ishare.iask.sina.com.cn/download.php?fileid=%s'%(fid),"")
        ref=new_referer and \
            "http://ishare.iask.sina.com.cn/download/explain.php?fileid=%s"%(fid) \
            or dlurl
        req.add_header('Referer',ref)
        retry=0
        while True:
            try:
                f=urllib2.urlopen(req)
            except urllib2.HTTPError,e:#print dir(e)
                if e.code==302: 
                    print "get file location(%s)"%fn
                    return e.hdrs['Location'],ref 
                print "opps~HTTPError(%d)"%(e.code)
            except Exception,ec:#py2.6+:except Exception as ec:
                print "\n  *_* can't locate file %s[%s]"%(fn,str(ec))
            else:
                print "\n  *_* can't locate file %s[http no redirection]"%fn
            if retry>3:
                print "\n  *_*retry too many times,it just failed"
                return
            else:
                retry+=1
                print "\n  retry %d(%d) after 2 secs"%(retry,3)
                time.sleep(2)
    def readPage(self,url,referer=None):
        print "analyzing "+url+"..pls wait",
        retry=0
        while True:
            try:
                req=urllib2.Request(url)
                if referer:
                    req.add_header('Referer',referer)
                str=urllib2.urlopen(req).read()
                print "->done"
                return str
            except IOError:
                if retry>3:
                    print "\nIO failure too many times,exiting,pls try later.."
                    sys.exit(1)
                else:
                    retry+=1
                    print "\nioerror,retry %d(%d) after 1 secs"%(retry,3)
                    time.sleep(1)
    def getUserFileList(self):
        self.initData() 
        self.uid=self.UID.get()
        if not self.uid:
            tkMessageBox.showerror("!!", "uid为空")
            return
        #get user info
        url="http://iask.sina.com.cn/user/user.php?uid=%s"%(self.uid)
        htm=self.readPage(url,"http://iask.sina.com.cn/user/score_list.php?uid=%s"%(self.uid))
        self.unm=re.compile(u'<title>(.+?) - 个人中心</title>'.encode('cp936'),re.I).search(htm).group(1).decode('cp936').encode('utf_8')
        self.recurseAddLists(0,0,'')
        self.InitFileView()
    def recurseAddLists(self,pfdid,fdid,fdnm):
        print "we are now at %s"%(fdnm)
        #get page number
        url="http://iask.sina.com.cn/u/%s/ish?folderid=%d"%(self.uid,fdid)
        htm=self.readPage(url)
        mo=re.compile(u'page=(\d+)[^>]+?>尾页</a>'.encode('cp936'),re.I).search(htm)
        if mo: pg=int(mo.group(1))
        else: pg=0
        for i in range(pg+1): #get file list
            url="http://iask.sina.com.cn/u/%s/ish?folderid=%d&page=%d"%(self.uid,fdid,i)
            htm=self.readPage(url)
            #first get files
            reo=re.compile(u'<li class="heading3"><img.+?><a href="(.+?)" title="(.+?)".+?<li class="size">(.+?)</li>.+?(\d+)分'.encode('cp936'),re.I|re.S)
            flist=reo.findall(htm)
            for finfo in flist:
                finfo=list(finfo)
                if int(finfo[3])!=0:finfo.append(self._FS_GRADE)
                else:finfo.append(self._FS_SELED)
                self.filelist.append(finfo)
            #then travel into subfolds
            reo=re.compile(u'<li class="heading3"><a href=".+?folderid=(.+?)".+?><img.+?>(.+?)</a>'.encode('cp936'),re.I|re.S)
            fdlist=reo.findall(htm)
            for fdinfo in fdlist:
                subid=(int)(fdinfo[0])
                if subid != pfdid:
                    self.recurseAddLists(fdid,subid,'%s_%s'%(fdnm,fdinfo[1]))
    #___________________________UI update
    def InitFileView(self):
        self.pgNo=0
        self.UID.set(self.uid)
        self.loadUserInfo()
        self.loadSelInfo()
        self.loadFilterInfo()
        self.updateFlist()
        self.updateSelStatus()
    def loadUserInfo(self):
        for f in self.UINFO.pack_slaves(): f.destroy()
        Label(self.UINFO,text='%s(%s)'%(self.unm,self.uid),font=('system',6)).pack(side='left')
        self.new_referer=IntVar()
        Checkbutton(self.UINFO,variable=self.new_referer).pack(side='right')
        Button(self.UINFO,text='file id list',command=self.exportFid).pack(side='right')
        Button(self.UINFO,text='生成下载列表',command=self.exportLst).pack(side='right')
        Button(self.UINFO,text='导入以前生成的lst',command=self.importLst).pack(side='right')
    def loadSelInfo(self):
        for o in self.SELINFO.pack_slaves():o.destroy()
        vo=IntVar()
        Checkbutton(self.SELINFO,text="反选\n(当前页)",font=('system',6),command=lambda :self.rSelByPage()).pack(side='left')
        Checkbutton(self.SELINFO,text="全选\n(当前页)",font=('system',6),variable=vo,command=lambda vo=vo:self.aSelByPage(vo)).pack(side='left')
        self.SELSTATUS=Label(self.SELINFO,font=('system',9))
        self.SELSTATUS.pack(side="left",expand=1)
        va=IntVar()
        Checkbutton(self.SELINFO,text="反选\n(所有页)",font=('system',6),command=lambda :self.rSelAll()).pack(side='right')
        Checkbutton(self.SELINFO,text="全选\n(所有页)",font=('system',6),variable=va,command=lambda vo=va:self.aSelAll(vo)).pack(side='right')
    def loadFilterInfo(self):
        for o in self.FILTER.pack_slaves():o.destroy()
        filter=StringVar()
        Entry(self.FILTER,textvariable=filter).pack(side='left')
        vo=IntVar()
        Checkbutton(self.FILTER,text="过滤",font=('system',6),variable=vo,command=lambda so=filter,vo=vo:self.doFilter(so,vo)).pack(side='left')
    def updateFlist(self): #list:[url,name,size,grade,status]
        flist=self.getViewList()
        for f in self.FLIST.grid_slaves(): f.destroy()
        for i in range(self.pgCap):
            id=self.pgNo*self.pgCap+i
            if id>len(flist)-1:break
            else:
                fInfo=flist[id]
                rowfont=('system',8)
                #select
                vo=IntVar()
                CK=Checkbutton(self.FLIST,font=rowfont,variable=vo,command=lambda id=id,vo=vo:self.selone(id,vo))
                CK.grid(row=i,column=0)
                if flist[id][4]==self._FS_GRADE:
                    CK.config(state=DISABLED,bg='#dddddd')
                else:
                    vo.set(flist[id][4])
                #nameenumerate
                NAME=Label(self.FLIST,font=rowfont)
                NAME.grid(row=i,column=1,sticky=W)
                NAME["text"]=fInfo[1].decode('cp936').encode('utf_8')
                #def handler(event,self=self,index=id):return self.goURL(event,index) NAME.bind('<Button-1>',handler)
                NAME.bind('<Button-1>',lambda e,index=id:self.goURL(e,index))
                #size
                SZ=Label(self.FLIST,font=rowfont)
                SZ.grid(row=i,column=2,sticky=W)
                SZ["text"]=fInfo[2].decode('cp936').encode('utf_8')
                #grade
                GRADE=Label(self.FLIST,font=rowfont)
                GRADE.grid(row=i,column=3,sticky=W)
                GRADE["text"]=fInfo[3].decode('cp936').encode('utf_8')
                #action
                if flist[id][4]!=self._FS_GRADE:
                    DL=Button(self.FLIST,font=rowfont,pady=0,text='download')
                    DL['command']=lambda index=id:self.dlFile(index)
                    DL.grid(row=i,column=4,sticky=W)
        #update index view
        for f in self.INDEX.grid_slaves(): f.destroy()
        bs=self.pgBsz=20
        self.pgCt=int(math.ceil(float(len(flist))/self.pgCap))
        for i in range(self.pgNo/bs*bs,min((self.pgNo/bs+1)*bs,self.pgCt)):
            s=Label(self.INDEX,text=i)
            s.grid(row=0,column=i%self.pgBsz+1,padx=5)
            if i== self.pgNo:
                s['fg']='#aa0000'
            else:
                s.bind('<Button-1>',lambda e,index=i:self.SelPage(e,index))
        s=Label(self.INDEX,text='<<')
        s.grid(row=0,column=0,padx=5)
        s.bind('<Button-1>',self.PrevBlock)
        s=Label(self.INDEX,text='>>')
        s.grid(row=0,column=bs+1,padx=5)
        s.bind('<Button-1>',self.NextBlock )

        Label(self.INDEX,text='page %d/%d'%(self.pgNo,self.pgCt-1)).grid(row=0,column=self.pgBsz+2)

        self.FLIST.bind('<Key-Up>',self.PrevBlock)
        self.FLIST.bind('<Key-Down>',self.NextBlock)
        self.FLIST.bind('<Key-Left>',lambda e:self.SelPage(e,self.pgNo-1))
        self.FLIST.bind('<Key-Right>',lambda e:self.SelPage(e,self.pgNo+1))
        self.FLIST.focus_set()
        self.STATUS['text']="←/→:前/后页   ↑/↓:前/后块"
    def updateSelStatus(self):
        flist=self.getViewList()
        nsel=0
        for finfo in flist:
            if finfo[4]==self._FS_SELED:nsel+=1
        self.SELSTATUS["text"]='%d/%d selected'%(nsel,len(flist))
    #______________________UI handler
    def selone(self,index,vo):
        flist=self.getViewList()
        flist[index][4]=vo.get()
        self.updateSelStatus()
    def rSelByPage(self):
        flist=self.getViewList()
        for i in range(self.pgCap):
            id=self.pgNo*self.pgCap+i
            if id>len(flist)-1:break
            else:
                if flist[id][4]!=self._FS_GRADE:flist[id][4]=int(not flist[id][4])
        self.updateSelStatus()
        self.updateFlist()
    def aSelByPage(self,vo):
        flist=self.getViewList()
        for i in range(self.pgCap):
            id=self.pgNo*self.pgCap+i
            if id>len(flist)-1:break
            else:
                flist[id][4]=int(vo.get())
        self.updateSelStatus()
        self.updateFlist()
    def rSelAll(self):
        flist=self.getViewList()
        for finfo in flist:
            if finfo[4]!=self._FS_GRADE:finfo[4]=int(not finfo[4])
        self.updateSelStatus()
        self.updateFlist()
    def aSelAll(self,vo):
        flist=self.getViewList()
        for finfo in flist:
            finfo[4]=int(vo.get())
        self.updateSelStatus()
        self.updateFlist()
    def goURL(self,event,index):
        webbrowser.open(self.filelist[index][0].decode('cp936').encode('utf_8'))
    def dlFile(self,index):
        thread.start_new_thread(self.tdlFile,(index,))
    def doFilter(self,so,vo):
        if vo.get():
            if so.get():
                self.search,self.searchlist=True,[]
                #print type(so.get())
                for f in (self.filelist):
                    find=re.compile(so.get().encode('cp936'),re.I).search(f[1])
                    if find:
                        self.searchlist.append(f)
                self.pgNo=0
                self.updateFlist()
        else:
            if(self.search):self.search=False
            self.updateFlist()
        self.updateSelStatus()
    def SelPage(self,event,index): #index=int(event.widget["text"])
        if index>=0 and index<self.pgCt:
            self.pgNo=index
            self.updateFlist()
    def NextBlock(self,e):
        self.SelPage(e,(self.pgNo/self.pgBsz+1)*20)
    def PrevBlock(self,e):
        self.SelPage(e,(self.pgNo/self.pgBsz-1)*20)
    def exportFid(self):
        flist=self.getViewList()
        s=map(lambda r:re.search('(\d+?)\.html',r[0].decode('cp936').encode('utf_8')).group(1),\
            filter(lambda r:r[4]==self._FS_SELED,flist))
        fn=tkFileDialog.asksaveasfilename(filetypes=[("lst","*.lst")],defaultextension="lst",initialfile='%s(%s)'%(self.unm,self.uid))
        if fn:
            f=open(fn,'w')
            f.write(str(s));
            f.flush()
            f.close()
        print "done"
    def exportLst(self):
        new_referer=self.new_referer.get()
        flist=self.getViewList()
        if not flist:
            if not tkMessageBox.askokcancel("!!", "文件列表为空"):return
        fn=tkFileDialog.asksaveasfilename(filetypes=[("lst","*.lst")],defaultextension="lst",initialfile='%s(%s)'%(self.unm,self.uid))
        if fn:
            f=open(fn,'w')
            for finfo in flist:
                if finfo[4]==self._FS_SELED:
                    url,referer=self.getDlink(finfo,new_referer)
                    if url:
                        f.write(url+'|'+referer+'||\n')
                    time.sleep(0.5)
            f.flush()
            f.close()
            print 'done'
            tkMessageBox.showinfo("ok",'成功生成下载列表文件\n使用QQ旋风导入')
    def importLst(self):
        flist=self.getViewList()
        fn=tkFileDialog.askopenfilename(filetypes=[("lst","*.lst"),("all files", "*")])
        found=0
        if fn:
            f=open(fn,'r')
            while 1:
                ln=f.readline()
                if not ln:break
                url=ln.split('|')[1]
                for id,fd in enumerate(flist):
                    if fd[0]==url:
                        found+=1
                        flist[id][4]=self._FS_SELED
                        break
            print "%d found"%found
            self.InitFileView()
    def saveFlst(self):
        if not self.filelist:
            tkMessageBox.showerror('!!','文件列表为空')
            return
        fn=tkFileDialog.asksaveasfilename(filetypes=[('flist','*.flst'),('all files', '*')],defaultextension='flst',initialfile='%s(%s)'%(self.unm,self.uid))
        if fn:
            data=[self.version,self.uid,self.unm,self.filelist]
            cPickle.dump(data,open(fn,"w"))
            print 'save flst done'
    def loadFlst(self):
        fn=tkFileDialog.askopenfilename(filetypes=[("flst","*.flst"),("all files", "*")])
        if fn:
            data=cPickle.load(open(fn,"r"))
            self.initData()
            if(isinstance(data,list)) and len(data)==4:
                if isinstance(data[0],float):
                    self.version,self.uid,self.unm,self.filelist=data
                else:#compatible with prev version
                    self.uid,self.unm=data[0],data[1]
                    for id in range(len(data[2])):
                        finfo=data[3][id]
                        finfo=list(finfo)
                        finfo.append(data[2][id])
                        self.filelist.append(finfo)
            else:tkMessageBox.showerror('!!','文件格式错误')
            self.InitFileView()
    def mode1(self):
        for w in self.PARAM.pack_slaves(): w.pack_forget()
        Label(self.PARAM,text='uid:',font=('system',10)).pack(side='left')
        self.UID=StringVar()
        Entry(self.PARAM,textvariable=self.UID).pack(side='left')
        Button(self.PARAM,text='生成文件列表(.flst)',font=('system',10),command=self.getUserFileList).pack(side='left')
        Button(self.PARAM,text='打开文件列表..',command=self.loadFlst).pack(side='left')
        Button(self.PARAM,text='保存文件列表..',command=self.saveFlst).pack(side='left')
app=AppWin()
app.mainloop()

"""#TODO:login support-more than 0 point downloads
def ishareLogin():
    cookie_pc=urllib2.HTTPCookieProcessor()
    urllib2.install_opener(urllib2.build_opener(cookie_pc))

    get_uid_url='http://rw.sina.com.cn/r?from=zhishi'
    urllib2.urlopen(get_uid_url)

    login_req_url='http://ishare.iask.sina.com.cn/login/log_com.php'
    f=urllib2.urlopen(login_req_url,'U_Loginname=test&U_Pass=test')

    #for coki in cookie_pc.cookiejar: print coki.name+':'+coki.value
def getLoginStatus():
    login_status_url='http://ishare.iask.sina.com.cn/login/log.php'
    f=urllib2.urlopen(login_status_url)
    #print f.info()
    htm=f.read()
    print htm
"""
