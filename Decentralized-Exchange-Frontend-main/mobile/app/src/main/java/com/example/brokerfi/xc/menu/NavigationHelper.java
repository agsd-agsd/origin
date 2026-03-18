package com.example.brokerfi.xc.menu;

import static androidx.core.content.ContextCompat.startActivity;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Rect;
import android.net.Uri;
import android.os.Handler;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.view.inputmethod.InputMethodManager;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.PopupWindow;
import android.widget.RelativeLayout;
import android.widget.Toast;

import androidx.annotation.Nullable;

import com.example.brokerfi.R;
import com.example.brokerfi.xc.AtvActivity;
import com.example.brokerfi.xc.MenuActivity;
import com.example.brokerfi.xc.QRCode.Capture;
import com.example.brokerfi.xc.ReceiveActivity;
import com.example.brokerfi.xc.SendActivity;
import com.example.brokerfi.xc.SettingActivity;
import com.example.brokerfi.xc.WelcomeBackActivity;
import com.example.brokerfi.xc.tool.UnitConverter;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

public class NavigationHelper{
    private ImageView menu;
    private RelativeLayout action_bar;
    private Context context;

    private boolean isIcon1 = true;
    private boolean isPopupVisible = false;
    private View customView;
    private int action_bar_height;
    private RelativeLayout sendlist;
    private RelativeLayout receivelist;
    private RelativeLayout activitylist;
    private RelativeLayout setlist;
    private RelativeLayout supportlist;
    private RelativeLayout locklist;
    private PopupWindow popupWindow;
    boolean hasExecuted = false; // 保证popupmenu只被初始化一次

    //这里实现自定义弹出式菜单
    public NavigationHelper(ImageView menu, RelativeLayout action_bar,Context context) {
        this.menu = menu;
        this.action_bar = action_bar;
        this.context = context;

        // 设置导航栏顶部间距
        int status_bar_height = getStatusBarHeight(context);//考虑状态栏
        int marginTop = status_bar_height + UnitConverter.dpToSp(context,2);
        //因为导航栏的parent有可能是linearlayout和relativelayout两种情况，所以需要分情况设置参数
        if (action_bar.getParent() instanceof RelativeLayout) {
            RelativeLayout.LayoutParams params = new RelativeLayout.LayoutParams(
                    RelativeLayout.LayoutParams.MATCH_PARENT, RelativeLayout.LayoutParams.WRAP_CONTENT);
            params.setMargins(0, marginTop, 0, 0);
            this.action_bar.setLayoutParams(params);
        } else if (action_bar.getParent() instanceof LinearLayout) {
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            params.setMargins(0, marginTop, 0, 0);
            this.action_bar.setLayoutParams(params);
        }
        //设置自定义的menu布局
        customView = LayoutInflater.from(context).inflate(R.layout.menu, null);
        //获取action_bar高度前保证action_bar的布局完成
        this.action_bar.getViewTreeObserver().addOnGlobalLayoutListener(new ViewTreeObserver.OnGlobalLayoutListener() {
            @Override
            public void onGlobalLayout() {
                if (!hasExecuted) {
                    action_bar_height = action_bar.getHeight();
                    int height;
                    // 在这里使用控件的高度
                    DisplayMetrics displayMetrics = new DisplayMetrics();
                    ((Activity) context).getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
                    int screenHeight = displayMetrics.heightPixels;
                    Rect rect = new Rect();
                    ((Activity) context).getWindow().getDecorView().getWindowVisibleDisplayFrame(rect);
                    int usableScreenHeight = rect.height();
                    //因为不同版本的安卓手机，screenHeight获取的范围不同
                    if(usableScreenHeight == screenHeight){
                        height = (int) (screenHeight - action_bar_height );
                    }else {
                        height = (int) (screenHeight - action_bar_height - marginTop );
                    }

                    popupWindow = new PopupWindow(customView, ViewGroup.LayoutParams.MATCH_PARENT, height, false);
                    hasExecuted = true; // 设置标志为已执行
                }
            }
        });
        //声明布局中的组件
        intCustomView();
        //点击menu icon时执行的动作
        menu.setOnClickListener(view -> {
            if (isKeyboardShown()) {
                hideKeyboard(); // 隐藏输入法
                new Handler().postDelayed(() -> {
                    toggleMenuIcon();
                    togglePopupVisibility(); // 在一定延迟后显示PopupWindow
                }, 100); // 延迟时间可以根据需要调整
            }else{
                toggleMenuIcon();
                togglePopupVisibility();

            }
        });

    }
    //customView 上面布局的定义
    private void intCustomView(){
        sendlist = customView.findViewById(R.id.sendlist);
        receivelist = customView.findViewById(R.id.receivelist);
        activitylist = customView.findViewById(R.id.activitylist);
        setlist = customView.findViewById(R.id.setlist);
        supportlist = customView.findViewById(R.id.supportlist);
        locklist = customView.findViewById(R.id.locklist);

        supportlist.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                String url = "https://www.blockemulator.com";

                // 创建一个Intent，用于启动浏览器Activity
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));

                // 检查设备上是否有能够处理该Intent的应用（通常是浏览器）
                if (intent.resolveActivity(context.getPackageManager()) != null) {
                    // 启动Intent，打开浏览器并导航到指定URL
                    context.startActivity(intent);
                } else {
                    // 若无应用能处理该Intent，则向用户显示一个错误消息
                    Toast.makeText(context, "无法打开网页，请检查您的浏览器设置。", Toast.LENGTH_LONG).show();
                }
            }
        });

        locklist.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent intent = new Intent(context, WelcomeBackActivity.class);
                context.startActivity(intent);
            }
        });

        sendlist.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 在这里打开摄像头
                IntentIntegrator intentIntegrator = new IntentIntegrator((Activity) context);
                intentIntegrator.setPrompt("For flash use volume up key");
                intentIntegrator.setBeepEnabled(true);
                intentIntegrator.setOrientationLocked(true);
                intentIntegrator.setCaptureActivity(Capture.class);
                intentIntegrator.initiateScan();

            }
        });
        receivelist.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 在这里执行跳转到另一个页面的操作
                Intent intent = new Intent(context, ReceiveActivity.class);
                context.startActivity(intent);

            }
        });
        activitylist.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 在这里执行跳转到另一个页面的操作
                Intent intent = new Intent(context, AtvActivity.class);
                context.startActivity(intent);

            }
        });
        setlist.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 在这里执行跳转到另一个页面的操作
                Intent intent = new Intent(context, SettingActivity.class);
                context.startActivity(intent);

            }
        });
    }




    private void toggleMenuIcon() {
        if (isIcon1) {
            menu.setImageResource(R.drawable.up_circle);
        } else {
            menu.setImageResource(R.drawable.action_menu_30);
        }
        isIcon1 = !isIcon1;
    }

    private void togglePopupVisibility() {
        DisplayMetrics displayMetrics = new DisplayMetrics();
        ((Activity) context).getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
        int screenHeight = displayMetrics.heightPixels;

        if (!isPopupVisible) {
            int yOffset = (int)(action_bar_height - menu.getHeight()) / 2;
            popupWindow.showAsDropDown(menu, 0, yOffset);

        } else {
            popupWindow.dismiss();
        }
        isPopupVisible = !isPopupVisible;
    }

    private void hideKeyboard() {
        InputMethodManager imm = (InputMethodManager) context.getSystemService(Context.INPUT_METHOD_SERVICE);
        imm.hideSoftInputFromWindow(menu.getWindowToken(), 0);
    }
    //检查输入法是否在显示
    private boolean isKeyboardShown() {
        InputMethodManager imm = (InputMethodManager) context.getSystemService(Context.INPUT_METHOD_SERVICE);
        return imm.isAcceptingText();
    }
    //获取顶部状态栏的高度
    public static int getStatusBarHeight(Context context) {
        int result = 0;
        int resourceId = context.getResources().getIdentifier("status_bar_height", "dimen", "android");
        if (resourceId > 0) {
            result = context.getResources().getDimensionPixelSize(resourceId);
        }
        return result;
    }






}
