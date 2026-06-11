---
title: DevC++使用手册
description: 
published: true
date: 2024-09-08T10:11:28.198Z
tags: 
editor: markdown
dateCreated: 2024-08-26T10:51:50.670Z
---



# 一、DevC++安装包下载

因DevC++是开源的，在网络上直接搜索DevC++或DevCpp，会出来比较多的版本，有些是二级开发，这里还是推荐安装官方版本：
- [DevCpp5.11_TDM](https://pan.baidu.com/s/1DKxZcWmU27CfcaWZd3vvcA?pwd=f9dm){target="_blank"}

Tabby是一个现代化的先进的跨平台终端工具，可以用来替代Windows的cmd窗口工具或者是PowerShell工具。具体使用文档和下载链接如下：
- [Tabby使用](/courses_resource/cloud_usage/快速使用云环境)
- [Tabby安装文件下载](https://pan.baidu.com/s/1BmCOxvg9SC4JPBolnoAvmw?pwd=46fk){target="_blank"}

# 二、安装注意点:安装路径配置
整个安装过程和常规软件安装一样，跟着向导next就可以。
在碰到安装路径选择时，优先推荐安装到C或D盘根目录下的Dev-Cpp，此设置主要是在编译程序时路径名中没有中文和空格。
![devcpp_installpath_root.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/devcpp_installpath_root.png)


# 三、调整编译器，支持C99标准，方便使用更多语言特性

## 3.1 从菜单进入编译设置：

![compiler_setup1.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup1.png)

## 3.2 打开编译选项窗口后，按下图顺序设置，选择C99标准

![compiler_setup2.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup2.png)

## 3.3 测试C99标准是否生效

编译执行如下代码是否正常：

```
#include <stdio.h>
#include <stdlib.h>

int main(){
	for(int i=0;i<3;i++){
		printf("%d,hello world!\n",i);
	}
	return 0;
}
```

在编译日志中会看到标准的启用：

![compiler_setup3.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup3.png)
# 四、创建工程
## 4.1、通过菜单:文件→新建→项目,打开新建窗口
![create_new_project.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/create_new_project.png)
## 4.2、在新建窗口中选择“Console Application”，C项目，项目名称优先全英文
![new_project_setup.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/new_project_setup.png)
## 4.3、项目保存路径推荐(尽量不使用中文路径)：
![new_project_savepath.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/new_project_savepath.png)
## 4.4、创建完成后，可添加打印程序行，通过点击菜单栏的编译运行或F11，在终端输出hello world!
![new_project_helloworld.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/new_project_helloworld.png)
![new_project_helloworld2.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/new_project_helloworld2.png)


> 恭喜，DevCPP安装成功，并能正常运行C程序。{.is-success}


# 五、下载并添加SDL2图形界面库到DevCPP
- [SDL2压缩包](https://pan.baidu.com/s/1CLNwxPlxeo4fH-DJCa0E5w?pwd=f4h5){target="_blank"}
- [SDL2_ttf压缩包](https://pan.baidu.com/s/14EeuxYcg_UBjHDa3-CIUeA?pwd=9m3g){target="_blank"}


# 六、解压SDL2-devel-2.30.6-mingw.zip，并将里面的SDL2-2.30.6目录复制到Dev-Cpp目录：
![sdl2_folder_save.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/sdl2_folder_save.png)

# 七、配置DevCPP的编译器，添加SDL2库及包含文件
## 7.1 选中工具→编译选项，打开配置窗口。
![compiler_setup1.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup1.png)
## 7.2 在编译器选项配置窗口下方的“在连接器命令行加入以下命令”编辑框中输入以下链接库：
![compiler_setup4.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup4.png)

内容可以从下方复制
```
-lmingw32 -lsdl2main -lsdl2
```
> 这里要注意两点：
减号-后面是小写L，不是数字1️⃣，也不是i。
这三个库的顺序不可变。

## 7.3 设置编译器标准为C99
![compiler_setup2.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup2.png)

## 7.4 进入目录标签添加头文件路径和库文件路径
打开“目录”标签，并选中下面的“库”标签
![compiler_setup5.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup5.png)
找到sdl2的lib目录
![project_setup_lib_path_2.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/project_setup_lib_path_2.png)
![compiler_setup6.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup6.png)
![compiler_setup7.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup7.png)

按上面的相同的方法，将C包含文件目录添加上：
![compiler_setup9.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup9.png)

![project_setup_include_path_3.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/project_setup_include_path_3.png)
![compiler_setup8.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/compiler_setup8.png)

完成以上步骤后，点项目选项窗口的确定按钮保存关闭窗口。

## 7.4 从SDL2-2.30.6/x86_64-mingw32/bin/目录中复制SDL2.dll到DevCPP的执行目录C:\Dev-Cpp\MinGW64\bin。
> 特别提醒：不可以复制SDL2-2.30.6/i686-w64-mingw32/bin/目录中的SDL2.dll{.is-success}

![sdl2.dll_copy.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/sdl2.dll_copy.png)

# 八、测试SDL2是否正常
将如下代码复制到项目的源码文件中：

```c
#include <SDL2/SDL.h>
#include <stdbool.h>

int main(int argc, char* argv[]) {
    // 初始化 SDL
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        SDL_Log("SDL could not initialize! SDL_Error: %s\n", SDL_GetError());
        return 1;
    }

    // 创建窗口
    SDL_Window* window = SDL_CreateWindow("SDL2 Square", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 800, 600, SDL_WINDOW_SHOWN);
    if (!window) {
        SDL_Log("Window could not be created! SDL_Error: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    // 创建渲染器
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) {
        SDL_Log("Renderer could not be created! SDL_Error: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    // 主循环标志
    bool running = true;
    SDL_Event event;

    while (running) {
        // 处理事件
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                running = false;
            }
        }

        // 清空渲染器
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255); // 黑色背景
        SDL_RenderClear(renderer);

        // 绘制正方形
        SDL_Rect square = { 350, 250, 100, 100 }; // 正方形的位置和大小
        SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255); // 红色
        SDL_RenderFillRect(renderer, &square);

        // 呈现渲染结果
        SDL_RenderPresent(renderer);
        
        SDL_Delay(16);//60Hz 刷新
    }

    // 清理资源
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();

    return 0;
}

```
保存后按F11编译运行，可得到图形显示效果：
![sdl2_draw_square_1.png](/wiki_images/courses_resource/c_language/devcpp_usage_images/sdl2_draw_square_1.png)

> 恭喜，SDL2图形库安装配置成功，可继续{.is-success}