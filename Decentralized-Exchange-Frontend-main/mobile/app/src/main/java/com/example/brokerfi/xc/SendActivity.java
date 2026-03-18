package com.example.brokerfi.xc;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.Toast;

import com.example.brokerfi.R;
import com.example.brokerfi.xc.menu.NavigationHelper;
import com.example.brokerfi.xc.net.BaseUrl;
import com.example.brokerfi.xc.net.MyCallBack;
import com.example.brokerfi.xc.net.OkhttpUtils;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

import org.json.JSONException;
import org.json.JSONObject;

public class SendActivity extends AppCompatActivity {
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    private ImageView menu;
    private RelativeLayout action_bar;
    private EditText edt_sendfrom;
    private EditText edt_sendto;
    private EditText edt_amount;
    private EditText edt_fee;
    private NavigationHelper navigationHelper;
    private Button button;



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_send);

        intView();
        intEvent();


    }

    private void intView() {
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        edt_sendfrom = findViewById(R.id.edt_sendfrom);

        edt_sendfrom.setText(getAccountNumberFromSharedPreferences());
        edt_sendfrom.setEnabled(false);
        edt_sendto = findViewById(R.id.edt_sendto);
//        edt_sendto.setEnabled(false);
        edt_amount=findViewById(R.id.edt_amount);
        edt_fee= findViewById(R.id.edt_amount2);
        button=findViewById(R.id.btn_send);
    }

    private void intEvent(){
        navigationHelper = new NavigationHelper(menu, action_bar,this);

        String scannedData = getIntent().getStringExtra("scannedData");
        if(scannedData != null){
            edt_sendto.setText(scannedData);
        }
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // 点击按钮后执行 sendtx2network() 函数
                sendtx2network();
            }
        });

    }

    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
//        return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }
    private void sendtx2network(){

        String sendFrom = edt_sendfrom.getText().toString();
        String sendTo = edt_sendto.getText().toString();
        String amount = edt_amount.getText().toString();
        String fee = edt_fee.getText().toString();


        // 构造请求体，将数据打包成 JSON 格式
        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("from", sendFrom);
            requestBody.put("to", sendTo);
            requestBody.put("value", amount);
            requestBody.put("fee", fee);
        } catch (JSONException e) {
            e.printStackTrace();
            return; // 如果出现异常，直接返回，不执行网络请求
        }

        // 发起 POST 请求
        OkhttpUtils.getInstance().doPost(BaseUrl.SEND_TX_URL, requestBody.toString(), new MyCallBack() {
            @Override
            public void onSuccess(String result) {
                // 处理请求成功的情况
                // 在这里处理服务器返回的结果
                Log.d("result:", result);
                // 解析返回的 JSON 数据
                JSONObject jsonResponse = null;
                try {
                    jsonResponse = new JSONObject(result);
                } catch (JSONException e) {
                    e.printStackTrace();

                }
                Log.d("jsonResponse:", String.valueOf(jsonResponse));

                // 获取 balance 字段的内容
                String message = jsonResponse.optString("message");
                if("success".equals(message)){
                    Toast.makeText(SendActivity.this,"交易成功",Toast.LENGTH_LONG).show();
                }else{
                    String error = jsonResponse.optString("error");
                    Toast.makeText(SendActivity.this,"交易失败："+ error,Toast.LENGTH_LONG).show();
                }



            }

            @Override
            public Void onError(Exception e) {
                // 处理请求失败的情况
                // 在这里处理网络请求失败或其他错误
                Toast.makeText(SendActivity.this,"网络出错",Toast.LENGTH_LONG).show();
                return null;
            }
        });
    }
    public void onBackPressed() {
        Intent intent = new Intent(this, MainActivity.class);
        startActivity(intent);
        overridePendingTransition(R.anim.slide_in_from_left, R.anim.slide_out_to_right);
    }
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        IntentResult intentResult = IntentIntegrator.parseActivityResult(
                requestCode,resultCode,data
        );
        if (intentResult.getContents() != null){
            String scannedData = intentResult.getContents();
            Intent intent = new Intent(this,SendActivity.class);
            intent.putExtra("scannedData",scannedData);
            startActivity(intent);

        }
    }

}