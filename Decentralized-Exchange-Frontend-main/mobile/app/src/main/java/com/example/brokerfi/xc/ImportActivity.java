package com.example.brokerfi.xc;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.widget.Toast;

import com.example.brokerfi.R;

public class ImportActivity extends AppCompatActivity {
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_import);
        String address = getAccountNumberFromSharedPreferences();
        if (address != null){

            Intent intent = new Intent(ImportActivity.this, WelcomeBackActivity.class);
            startActivity(intent);

            // 获取当前Activity的上下文（或者你也可以使用getApplicationContext()）
//            Context context = this; // 如果你在Activity内部
//// 或者 Context context = getParentFragment().getActivity(); 如果你在Fragment内部
//
//// 创建一个Toast对象，设置要显示的文本和显示的时间长度（LENGTH_SHORT或LENGTH_LONG）
//            Toast toast = Toast.makeText(context, "导入成功！ 账户地址为："+address, Toast.LENGTH_SHORT);
//
//// 显示Toast
//            toast.show();
//
//            Handler handler = new Handler();
//
//            // 定义一个Runnable任务，该任务将在延迟后执行
//            Runnable runnable = new Runnable() {
//                @Override
//                public void run() {
//                    // 创建Intent并启动MainActivity
//                    Intent intent = new Intent(ImportActivity.this, MainActivity.class);
//                    startActivity(intent);
//                }
//            };
//
//            // 使用postDelayed方法延迟执行Runnable任务，参数为Runnable对象和延迟时间（毫秒）
//            handler.postDelayed(runnable, 3000);

//            Intent intent = new Intent();
//            intent.setClass(ImportActivity.this, MainActivity.class);
//            //跳转
//            startActivity(intent);
        }
    }


    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
//        return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }


}