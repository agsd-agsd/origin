package com.example.brokerfi.xc;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.UnderlineSpan;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.example.brokerfi.R;

import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class CreatePasswActivity extends AppCompatActivity {
    // 定义SharedPreferences的文件名和键
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    private static final String Pass = "password";
    private EditText new_passw;
    private EditText confirm_passw;
    private CheckBox checkBox;
    private Button btn_create;
    private TextView txw_underline;
    private SpannableString spannableString=null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_create_passw);
        intView();
        intEvent();

        String address = getAccountNumberFromSharedPreferences();
        if (address != null){

            // 获取当前Activity的上下文（或者你也可以使用getApplicationContext()）
//            Context context = this; // 如果你在Activity内部
//// 或者 Context context = getParentFragment().getActivity(); 如果你在Fragment内部
//
//// 创建一个Toast对象，设置要显示的文本和显示的时间长度（LENGTH_SHORT或LENGTH_LONG）
//            Toast toast = Toast.makeText(context, "找到已有账户！ 账户地址为："+address, Toast.LENGTH_SHORT);
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
//                    Intent intent = new Intent(CreatePasswActivity.this, MainActivity.class);
//                    startActivity(intent);
//                }
//            };
//
//            // 使用postDelayed方法延迟执行Runnable任务，参数为Runnable对象和延迟时间（毫秒）
//            handler.postDelayed(runnable, 3000);


            Intent intent = new Intent(CreatePasswActivity.this, WelcomeBackActivity.class);
            startActivity(intent);
    }
    }

    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
//        return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }


    private void intView() {
        new_passw = findViewById(R.id.new_passw);
        confirm_passw = findViewById(R.id.confirm_passw);
        checkBox = findViewById(R.id.checkbox);
        btn_create = findViewById(R.id.btn_create);
        txw_underline = findViewById(R.id.txw_underline);
    }

    private void intEvent(){

        String text = "Terms of use";
        spannableString = new SpannableString(text);
        spannableString.setSpan(new UnderlineSpan(), 0, text.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        txw_underline.setText(spannableString);


        btn_create.setOnClickListener(view -> {
            String newPassw = String.valueOf(new_passw.getText());
            String confirnPassw = String.valueOf(confirm_passw.getText());
            if(!checkBox.isChecked()){
                Toast.makeText(CreatePasswActivity.this, "请同意协议！", Toast.LENGTH_LONG).show();
                return;
            }
            if(newPassw==""){
                Toast.makeText(CreatePasswActivity.this, "密码不得为空！", Toast.LENGTH_LONG).show();
                return;
            }
            if(newPassw.length()<6){
                Toast.makeText(CreatePasswActivity.this, "密码最少6位！", Toast.LENGTH_LONG).show();
                return;
            }
            if(!newPassw.equals(confirnPassw)){
                Toast.makeText(CreatePasswActivity.this, "密码和确认密码不同！", Toast.LENGTH_LONG).show();
                return;
            }

                String address = generateAddress(newPassw + System.currentTimeMillis(), 40);
                System.out.println("create address: "+address);
                saveAccountNumberToSharedPreferences(address);
                savePasswd(newPassw);
                //创建意图对象
                Intent intent = new Intent();
                intent.setClass(CreatePasswActivity.this, SecretPhraseActivity.class);
                //跳转
                startActivity(intent);



        });
    }

    private void savePasswd(String accountNumber) {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = settings.edit();
        editor.putString(Pass, accountNumber);
        editor.apply();
    }

    private void saveAccountNumberToSharedPreferences(String accountNumber) {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = settings.edit();
        editor.putString(PREF_ACCOUNT_NUMBER, accountNumber);
        editor.apply();
    }

    @Override
    public void onBackPressed() {
        // 在这里执行你的自定义操作
        super.onBackPressed(); // 调用父类的方法以保持默认的返回行为
    }

    public static String generateAddress(String input, int length) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes("UTF-8"));
            BigInteger number = new BigInteger(1, hash);
            String hashedText = number.toString(16);
            // 如果需要的长度比哈希值的十六进制表示短，则截取
            // 如果需要的长度更长，则可能需要其他逻辑（如填充或添加其他信息）

            if(hashedText.length() > length){
                return hashedText.substring(0, length);
            }else {
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < length - hashedText.length(); i++) {
                    sb.append("0");
                }
                return  sb.toString()+hashedText;
            }
        } catch (NoSuchAlgorithmException | java.io.UnsupportedEncodingException e) {
            throw new RuntimeException(e);
        }
    }


}