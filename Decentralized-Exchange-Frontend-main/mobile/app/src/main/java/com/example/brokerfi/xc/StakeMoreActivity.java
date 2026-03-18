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
import android.widget.EditText;
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

import java.util.concurrent.atomic.AtomicBoolean;

public class StakeMoreActivity extends AppCompatActivity {

    private TextView stakemoretext;
    private EditText edt_sendfrom;
    private EditText edt_sendto;
    private EditText stakeamount;
    private Button btn_stake;
    private ImageView menu;
    private RelativeLayout action_bar;
    private NavigationHelper navigationHelper;
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    AtomicBoolean isBrokerBoolean = new AtomicBoolean();
    boolean flag = false;

    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
//        return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_stake_more);

        Intent intent = getIntent();

        // 使用 getStringExtra 方法从 Intent 中提取数据
        // 注意这里的 "extra_data" 必须与传递时使用的键名相同
        String receivedData = intent.getStringExtra("extra_data");
        if(receivedData!=null){
            flag=true;
        }else {

        }
        intView();
        intEvent();
    }

    private void intView() {
        edt_sendfrom = findViewById(R.id.edt_sendfrom);
        edt_sendto = findViewById(R.id.edt_sendto);
        btn_stake = findViewById(R.id.stakemorebtn);
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        stakeamount = findViewById(R.id.stakeamount);
        stakemoretext = findViewById(R.id.stakemoretext);
    }

    private void intEvent() {
        navigationHelper = new NavigationHelper(menu, action_bar, this);
        edt_sendfrom.setText(getAccountNumberFromSharedPreferences());

        edt_sendfrom.setEnabled(false);
        edt_sendto.setEnabled(false);
        edt_sendto.setText("Broker2Earn");


        OkhttpUtils.getInstance().doGet(BaseUrl.QueryIsBrokerURL + "?addr=" + getAccountNumberFromSharedPreferences(), new MyCallBack() {
            @Override
            public void onSuccess(String result) {
                Log.d("result:", result);

                // 解析返回的 JSON 数据
                JSONObject jsonResponse = null;
                try {
                    jsonResponse = new JSONObject(result);

                    String is_broker = jsonResponse.getString("is_broker");
                    if ("true".equals(is_broker)) {
                        isBrokerBoolean.set(true);
                        if(flag){
                            runOnUiThread(()->{
                                stakemoretext.setText("Stake");

                            });
                        }else {
                            runOnUiThread(()->{
                                stakemoretext.setText("Stake more");

                            });
                        }

                    } else {
                        isBrokerBoolean.set(false);
                        if(flag){
                            runOnUiThread(()->{

                                stakemoretext.setText("Stake");

                            });
                        }else {
                            runOnUiThread(()->{

                                stakemoretext.setText("Stake");

                            });
                        }

                    }

                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }

            @Override
            public Void onError(Exception e) {
                Toast.makeText(StakeMoreActivity.this, "网络出错", Toast.LENGTH_LONG).show();

                return null;
            }
        });



        btn_stake.setOnClickListener(view -> {



            OkhttpUtils.getInstance().doGet(BaseUrl.BecomeBrokerURL + "?addr=" + getAccountNumberFromSharedPreferences() + "&token=" + stakeamount.getText(), new MyCallBack() {
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
                                Toast.makeText(StakeMoreActivity.this, error, Toast.LENGTH_LONG).show();
                            }
                        } catch (Exception e) {
                            try {
                                String message = jsonResponse.getString("message");
                                if (message != null) {
                                    Toast.makeText(StakeMoreActivity.this, message, Toast.LENGTH_LONG).show();

                                    Handler h = new Handler();
                                    h.postDelayed(()->{
                                        //创建意图对象
                                        Intent intent = new Intent();
                                        intent.setClass(StakeMoreActivity.this, AfterBrokerActivity.class);
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
                    Toast.makeText(StakeMoreActivity.this, "网络出错", Toast.LENGTH_LONG).show();

                    return null;
                }
            });



        });
    }

    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        IntentResult intentResult = IntentIntegrator.parseActivityResult(
                requestCode, resultCode, data
        );
        if (intentResult.getContents() != null) {
            String scannedData = intentResult.getContents();
            Intent intent = new Intent(this, SendActivity.class);
            intent.putExtra("scannedData", scannedData);
            startActivity(intent);

        }
    }


}