/* Native WinPE text clipboard bridge over the private QEMU user network. No guest driver required. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define LIMIT (1024u*1024u)
static HWND owner;
static SOCKET channel;
static DWORD sequence;
static int write_all(const void *buf, DWORD size) {
 const char *p=buf; int n;
 while(size) { n=send(channel,p,(int)size,0);if(n<=0) return 0;p+=n;size-=(DWORD)n; }
 return 1;
}
static int send_text(const char *text, DWORD length) {
 unsigned char h[8]={'I','B','C','2',0,0,0,0};
 h[4]=length;h[5]=length>>8;h[6]=length>>16;h[7]=length>>24;
 return write_all(h,8) && (length==0xffffffffu || write_all(text,length));
}
static int set_clip(const char *text, int length) {
 if(memchr(text,0,length)) return 0;
 int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text,length,NULL,0);
 if(length && !n) return 0;
 HGLOBAL data=GlobalAlloc(GMEM_MOVEABLE,(n+1)*sizeof(wchar_t));
 if(!data) return 0;
 wchar_t *out=GlobalLock(data);
 if(!out) { GlobalFree(data);return 0; }
 if(n) MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text,length,out,n);
 out[n]=0;GlobalUnlock(data);
 if(!OpenClipboard(owner)) {GlobalFree(data);return 0;}
 int ok=EmptyClipboard() && SetClipboardData(CF_UNICODETEXT,data)!=NULL;
 CloseClipboard(); if(!ok) GlobalFree(data);
 sequence=GetClipboardSequenceNumber();return ok;
}
static char *get_clip(DWORD *size) {
 *size=0;
 if(!OpenClipboard(owner)) return NULL;
 HANDLE data=GetClipboardData(CF_UNICODETEXT);
 if(!data) {CloseClipboard();return NULL;}
 const wchar_t *text=GlobalLock(data);
 char *result=NULL;
 if(text) {
  int n=WideCharToMultiByte(CP_UTF8,0,text,-1,NULL,0,NULL,NULL);
  if(n>0 && n<=(int)LIMIT+1) {
   result=malloc(n);
   if(result) {WideCharToMultiByte(CP_UTF8,0,text,-1,result,n,NULL,NULL);*size=n-1;}
  }
  GlobalUnlock(data);
 }
 CloseClipboard();return result;
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE previous,LPWSTR args,int show) {
 (void)instance;(void)previous;(void)show;
 int test=wcsstr(args,L"--test")!=NULL;
 owner=CreateWindowExW(0,L"STATIC",L"IBS appunti",0,0,0,0,0,NULL,NULL,NULL,NULL);
 if(!owner) return 2;
 WSADATA winsock;
 if(WSAStartup(MAKEWORD(2,2),&winsock)) return 3;
 reconnect:
 channel=INVALID_SOCKET;
 for(;;) {
  channel=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);
  if(channel==INVALID_SOCKET) return 4;
  struct sockaddr_in address={0};address.sin_family=AF_INET;
  address.sin_port=htons(17625);address.sin_addr.s_addr=inet_addr("10.0.2.100");
  if(connect(channel,(struct sockaddr*)&address,sizeof(address))==0) break;
  closesocket(channel);Sleep(1000);
 }
 unsigned char *buffer=malloc(LIMIT+8);DWORD used=0;
 if(!buffer) return 6;
 sequence=GetClipboardSequenceNumber();
 if(!send_text(NULL,0xffffffffu)) return 7;
 DWORD last_ready=GetTickCount();int initialized=0;
 for(;;) {
  if(!initialized && GetTickCount()-last_ready>1000) {send_text(NULL,0xffffffffu);last_ready=GetTickCount();}
  DWORD got=0;
  fd_set readers;FD_ZERO(&readers);FD_SET(channel,&readers);
  struct timeval timeout={0,20000};
  int status=select(0,&readers,NULL,NULL,&timeout);
  if(status==SOCKET_ERROR) break;
  if(status>0) {
   int received=recv(channel,(char*)buffer+used,(int)(LIMIT+8-used),0);
   if(received<=0) break;
   got=(DWORD)received;
  }
  used+=got;
  while(used>=8) {
   if(memcmp(buffer,"IBC2",4)) goto done;
   DWORD length=(DWORD)buffer[4]|((DWORD)buffer[5]<<8)|((DWORD)buffer[6]<<16)|((DWORD)buffer[7]<<24);
   if(length>LIMIT) goto done;
   if(used<length+8) break;
   if(!set_clip((char*)buffer+8,length)) {Sleep(20);break;}
   initialized=1;
   if(test) {
    DWORD actual_size=0;char *actual=get_clip(&actual_size);
    if(!actual||actual_size!=length||memcmp(actual,buffer+8,length)) goto done;
    free(actual);
    const char *answer="WinRE -> Debian: caff\xc3\xa8, \xe2\x82\xac, \xe6\x96\x87\xe5\xad\x97\r\nseconda riga";
    if(!set_clip(answer,(int)strlen(answer))) goto done;
    DWORD n=0;char *data=get_clip(&n);
    if(!data||!send_text(data,n)) goto done;
    free(data);test=0;
   }
   used-=length+8;memmove(buffer,buffer+length+8,used);
  }
  if(sequence!=GetClipboardSequenceNumber()) {
   DWORD n=0;char *data=get_clip(&n);
   if(data) {if(!send_text(data,n)) {free(data);break;}free(data);sequence=GetClipboardSequenceNumber();}
  }
  MSG msg;while(PeekMessageW(&msg,NULL,0,0,PM_REMOVE)) {TranslateMessage(&msg);DispatchMessageW(&msg);}
  Sleep(50);
 }
 done: free(buffer);closesocket(channel);Sleep(500);goto reconnect;
}
