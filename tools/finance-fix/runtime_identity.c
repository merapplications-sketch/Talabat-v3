/* Local test runtime only: a single-id user namespace cannot run setuid/setgroups.
   Report nobody to PostgreSQL's root/owner checks; all actual OS rights remain unchanged.
   No network/auth/database calls are intercepted. Fixtures only, Unix socket only. */
#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <dlfcn.h>
uid_t getuid(void){return 65534;} uid_t geteuid(void){return 65534;}
int stat(const char*p,struct stat*s){int(*f)(const char*,struct stat*)=dlsym(RTLD_NEXT,"stat");int r=f(p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int lstat(const char*p,struct stat*s){int(*f)(const char*,struct stat*)=dlsym(RTLD_NEXT,"lstat");int r=f(p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int fstat(int p,struct stat*s){int(*f)(int,struct stat*)=dlsym(RTLD_NEXT,"fstat");int r=f(p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int stat64(const char*p,struct stat64*s){int(*f)(const char*,struct stat64*)=dlsym(RTLD_NEXT,"stat64");int r=f(p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int lstat64(const char*p,struct stat64*s){int(*f)(const char*,struct stat64*)=dlsym(RTLD_NEXT,"lstat64");int r=f(p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int fstat64(int p,struct stat64*s){int(*f)(int,struct stat64*)=dlsym(RTLD_NEXT,"fstat64");int r=f(p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int __xstat(int v,const char*p,struct stat*s){int(*f)(int,const char*,struct stat*)=dlsym(RTLD_NEXT,"__xstat");int r=f(v,p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int __lxstat(int v,const char*p,struct stat*s){int(*f)(int,const char*,struct stat*)=dlsym(RTLD_NEXT,"__lxstat");int r=f(v,p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
int __fxstat(int v,int p,struct stat*s){int(*f)(int,int,struct stat*)=dlsym(RTLD_NEXT,"__fxstat");int r=f(v,p,s);if(!r&&s->st_uid==0)s->st_uid=65534;return r;}
