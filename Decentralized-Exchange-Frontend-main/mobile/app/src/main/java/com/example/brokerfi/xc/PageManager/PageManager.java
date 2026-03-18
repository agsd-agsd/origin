package com.example.brokerfi.xc.PageManager;

import java.util.Stack;

public class PageManager {
    private static PageManager instance;
    private Stack<Class> pageStack = new Stack<>();

    private PageManager() {
    }

    public static PageManager getInstance() {
        if (instance == null) {
            instance = new PageManager();
        }
        return instance;
    }

    public void navigateTo(Class destinationPage) {
        // 在此处进行页面跳转逻辑，例如启动一个新的 Activity
        // 记录当前页面到堆栈
        pageStack.push(destinationPage);
    }

    public void navigateBackTo(Class destinationPage) {
        // 从页面堆栈中找到目标页面
        // 在堆栈中找到目标页面之前的页面并将它们出栈
        Stack<Class> tempStack = new Stack<>();
        Class currentPage;
        while (!pageStack.isEmpty()) {
            currentPage = pageStack.pop();
            if (currentPage == destinationPage) {
                break;
            }
            tempStack.push(currentPage);
        }
        // 将页面堆栈恢复为剩余的页面
        while (!tempStack.isEmpty()) {
            pageStack.push(tempStack.pop());
        }
        // 导航到目标页面
        // 这里可以实现跳转逻辑，例如启动一个新的 Activity
    }
}

