---
author: Gunn Kim
date: '2025-03-16T19:09:00.000Z'
draft: true
lastmod: '2025-03-16T19:09:00.000Z'
notion_id: 1b87522e-eb2f-81a5-95a4-f1fe66aa1b9d
title: Node.js from ‘구글크롬 V8’
---



```javascript
Last login: Thu Dec  8 09:41:22 on ttys000
gunn@macmini ~ % node -v
v19.2.0
gunn@macmini ~ % node
Welcome to Node.js v19.2.0.
Type ".help" for more information.
> var name = '김';
undefined
> name
'김'
> 1+1
2
> console.log('안녕')
안녕
undefined
>
```



Express 설치

```javascript
gunn@macmini study % cd todoapp
gunn@macmini todoapp % npm init
This utility will walk you through creating a package.json file.
It only covers the most common items, and tries to guess sensible defaults.

See `npm help init` for definitive documentation on these fields
and exactly what they do.

Use `npm install <pkg>` afterwards to install a package and
save it as a dependency in the package.json file.

Press ^C at any time to quit.
package name: (todoapp) 
version: (1.0.0) 
description: 
entry point: (index.js) server.js
test command: 
git repository: 
keywords: 
author: 
license: (ISC) 
About to write to /Users/gunn/study/todoapp/package.json:

{
  "name": "todoapp",
  "version": "1.0.0",
  "description": "",
  "main": "server.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "author": "",
  "license": "ISC"
}


Is this OK? (yes) 
npm notice 
npm notice New major version of npm available! 8.19.3 -> 9.2.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v9.2.0
npm notice Run npm install -g npm@9.2.0 to update!
npm notice 
gunn@macmini todoapp %
```


팩키지 설치 과정에서 폴더 권한 오류

```javascript
gunn@macmini todoapp % npm install -g nodemon
npm ERR! code EACCES
npm ERR! syscall mkdir
npm ERR! path /usr/local/lib/node_modules/nodemon
npm ERR! errno -13
npm ERR! Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules/nodemon'
npm ERR!  [Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules/nodemon'] {
npm ERR!   errno: -13,
npm ERR!   code: 'EACCES',
npm ERR!   syscall: 'mkdir',
npm ERR!   path: '/usr/local/lib/node_modules/nodemon'
npm ERR! }
npm ERR! 
npm ERR! The operation was rejected by your operating system.
npm ERR! It is likely you do not have the permissions to access this file as the current user
npm ERR! 
npm ERR! If you believe this might be a permissions issue, please double-check the
npm ERR! permissions of the file and its containing directories, or try running
npm ERR! the command again as root/Administrator.

npm ERR! A complete log of this run can be found in:
npm ERR!     /Users/gunn/.npm/_logs/2022-12-08T01_11_59_802Z-debug-0.log
gunn@macmini todoapp % sudo chown -R root:$(whoami) /usr/local/lib/node_modules/
Password:
Sorry, try again.
Password:
chown: gunn: illegal group name
gunn@macmini todoapp % sudo chown -R root:$(administrator) /usr/local/lib/node_modules/
zsh: command not found: administrator
gunn@macmini todoapp % sudo chown -R root:$(gunn) /usr/local/lib/node_modules/
zsh: command not found: gunn
gunn@macmini todoapp % sudo chown -R root:$(users) /usr/local/lib/node_modules/
chown: gunn: illegal group name
gunn@macmini todoapp % sudo chown -R root:$(김건우) /usr/local/lib/node_modules/
zsh: command not found: 김건우
gunn@macmini todoapp % sudo chmod -R 777 /usr/local/lib/node_modules/
gunn@macmini todoapp % npm install -g nodemon
npm ERR! code EACCES
npm ERR! syscall open
npm ERR! path /Users/gunn/.npm/_cacache/tmp/928b7445
npm ERR! errno -13
npm ERR! 
npm ERR! Your cache folder contains root-owned files, due to a bug in
npm ERR! previous versions of npm which has since been addressed.
npm ERR! 
npm ERR! To
```

```javascript
 permanently fix this problem, please run:
npm ERR!   sudo chown -R 501:20 "/Users/gunn/.npm"

npm ERR! Log files were not written due to an error writing to the directory: /Users/gunn/.npm/_logs
npm ERR! You can rerun the command with `--loglevel=verbose` to see the logs in your terminal
gunn@macmini todoapp % sudo chown -R 501:20 "/Users/gunn/.npm"
gunn@macmini todoapp % npm install -g nodemon                 
npm ERR! code EACCES
npm ERR! syscall symlink
npm ERR! path ../lib/node_modules/nodemon/bin/nodemon.js
npm ERR! dest /usr/local/bin/nodemon
npm ERR! errno -13
npm ERR! Error: EACCES: permission denied, symlink '../lib/node_modules/nodemon/bin/nodemon.js' -> '/usr/local/bin/nodemon'
npm ERR!  [Error: EACCES: permission denied, symlink '../lib/node_modules/nodemon/bin/nodemon.js' -> '/usr/local/bin/nodemon'] {
npm ERR!   errno: -13,
npm ERR!   code: 'EACCES',
npm ERR!   syscall: 'symlink',
npm ERR!   path: '../lib/node_modules/nodemon/bin/nodemon.js',
npm ERR!   dest: '/usr/local/bin/nodemon'
npm ERR! }
npm ERR! 
npm ERR! The operation was rejected by your operating system.
npm ERR! It is likely you do not have the permissions to access this file as the current user
npm ERR! 
npm ERR! If you believe this might be a permissions issue, please double-check the
npm ERR! permissions of the file and its containing directories, or try running
npm ERR! the command again as root/Administrator.

npm ERR! A complete log of this run can be found in:
npm ERR!     /Users/gunn/.npm/_logs/2022-12-08T01_22_49_474Z-debug-0.log
gunn@macmini todoapp % sudo chown -R gunn ~/.npm
gunn@macmini todoapp % sudo chown -R gunn ~/usr/local/lib/node_modules
chown: /Users/gunn/usr/local/lib/node_modules: No such file or directory
gunn@macmini todoapp % sudo chown -R gunn /usr/local/lib/node_modules 
gunn@macmini todoapp % npm install -g nodemon                         
npm ERR! code EACCES
npm ERR! syscall symlink
npm ERR! path ../lib/node_modules/nodemon/bin/nodemon.js
npm ERR! dest /usr/lo
```

```javascript
cal/bin/nodemon
npm ERR! errno -13
npm ERR! Error: EACCES: permission denied, symlink '../lib/node_modules/nodemon/bin/nodemon.js' -> '/usr/local/bin/nodemon'
npm ERR!  [Error: EACCES: permission denied, symlink '../lib/node_modules/nodemon/bin/nodemon.js' -> '/usr/local/bin/nodemon'] {
npm ERR!   errno: -13,
npm ERR!   code: 'EACCES',
npm ERR!   syscall: 'symlink',
npm ERR!   path: '../lib/node_modules/nodemon/bin/nodemon.js',
npm ERR!   dest: '/usr/local/bin/nodemon'
npm ERR! }
npm ERR! 
npm ERR! The operation was rejected by your operating system.
npm ERR! It is likely you do not have the permissions to access this file as the current user
npm ERR! 
npm ERR! If you believe this might be a permissions issue, please double-check the
npm ERR! permissions of the file and its containing directories, or try running
npm ERR! the command again as root/Administrator.

npm ERR! A complete log of this run can be found in:
npm ERR!     /Users/gunn/.npm/_logs/2022-12-08T01_25_17_821Z-debug-0.log
gunn@macmini todoapp % sudo chown -R gunn /usr/local/bin/nodemon      
chown: /usr/local/bin/nodemon: No such file or directory
gunn@macmini todoapp % sudo chown -R gunn /usr/local/bin        
gunn@macmini todoapp % npm install -g nodemon                   

added 33 packages, and audited 34 packages in 431ms

3 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
gunn@macmini todoapp %
```


```javascript
gunn@macmini todoapp % sudo chmod -R 777 ./
```


