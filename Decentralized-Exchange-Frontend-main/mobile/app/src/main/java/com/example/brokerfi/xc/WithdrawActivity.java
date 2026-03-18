package com.example.brokerfi.xc;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.TextView;
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

public class WithdrawActivity extends AppCompatActivity {
    private ImageView menu;
    private RelativeLayout action_bar;
    private NavigationHelper navigationHelper;
    private Button btn_withdraw;
    private TextView edt_sendfrom;
    private TextView edt_sendto;
    private TextView edt_amount;
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
//        return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_withdraw);
        intView();
        intEvent();
    }

    private void intView() {
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        btn_withdraw = findViewById(R.id.btn_withdraw);
        edt_sendfrom= findViewById(R.id.edt_sendfrom);
        edt_sendto= findViewById(R.id.edt_sendto);
        edt_amount=findViewById(R.id.edt_amount);
    }
    private void intEvent(){
        edt_sendfrom.setText("Broker2Earn");
        edt_sendfrom.setEnabled(false);
        edt_sendto.setText(getAccountNumberFromSharedPreferences());
        edt_sendto.setEnabled(false);
        edt_amount.setText("ALL");
        edt_amount.setEnabled(false);
        navigationHelper = new NavigationHelper(menu, action_bar,this);
        btn_withdraw.setOnClickListener(view -> {

            OkhttpUtils.getInstance().doGet(BaseUrl.WithdrawBrokerURL + "?addr=" + getAccountNumberFromSharedPreferences() , new MyCallBack() {
                @Override
                public void onSuccess(String result) {
                    Log.d("result:", result);

                    // 解析返回的 JSON 数据
                    JSONObject jsonResponse = null;
                    try {
                        jsonResponse = new JSONObject(result);
                        try {
                            String error = jsonResponse.getString("error");
                            if (error != null) {
                                Toast.makeText(WithdrawActivity.this, error, Toast.LENGTH_LONG).show();
                            }
                        } catch (Exception e) {
                            try {
                                String message = jsonResponse.getString("message");
                                if (message != null) {
                                    Toast.makeText(WithdrawActivity.this, message, Toast.LENGTH_LONG).show();

                                    Handler h = new Handler();
                                    h.postDelayed(()->{
                                        //创建意图对象
                                        Intent intent = new Intent();
                                        intent.setClass(WithdrawActivity.this, MainActivity.class);
                                        //跳转
                                        startActivity(intent);
                                    },3000);

                                }
                            } catch (Exception e1) {

                            }
                        }

                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public Void onError(Exception e) {
                    Toast.makeText(WithdrawActivity.this, "网络出错", Toast.LENGTH_LONG).show();

                    return null;
                }
            });




//            //创建意图对象
//            Intent intent = new Intent();
//            intent.setClass(WithdrawActivity.this, AfterBrokerActivity.class);
//            //跳转
//            startActivity(intent);
        });


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