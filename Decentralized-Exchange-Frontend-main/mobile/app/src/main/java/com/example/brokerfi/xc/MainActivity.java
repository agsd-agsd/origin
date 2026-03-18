package com.example.brokerfi.xc;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.Log;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.example.brokerfi.R;
import com.example.brokerfi.xc.menu.NavigationHelper;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;
import com.example.brokerfi.xc.net.*;

import org.json.JSONException;
import org.json.JSONObject;

import okhttp3.OkHttpClient;
import okhttp3.Request;

public class MainActivity extends AppCompatActivity {
    // 定义SharedPreferences的文件名和键
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    private ImageView menu;
    private RelativeLayout action_bar;
    private ImageView buy;
    private ImageView send;
    private ImageView swap;
    private ImageView broker;
    private LinearLayout support;
    private NavigationHelper navigationHelper;
    private RelativeLayout sendlist;
    private RelativeLayout receivelist;
    private RelativeLayout activitylist;
    private RelativeLayout setlist;
    private RelativeLayout supportlist;
    private RelativeLayout locklist;
    private TextView accountstate;
    private TextView tsv_dollar;
    private TextView e20cAccountState;
    // private OkHttpClient httpClient;

    private volatile boolean flag = false;

    @Override
    protected void onDestroy() {
        super.onDestroy();
        flag = true;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        intView();
        intEvent();
        // 初始化 OkHttpClient
        // httpClient = new OkHttpClient();
        // 在页面创建时，自动发送 GET 请求获取账户状态
        new Thread(() -> {
            while (true) {
                if (flag) {
                    break;
                }
                fetchAccountStatus();
                try {
                    Thread.sleep(500);
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
            }
        }).start();
    }

    private void intView() {
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        buy = findViewById(R.id.buy);
        send = findViewById(R.id.send);
        swap = findViewById(R.id.swap);
        broker = findViewById(R.id.broker);
        support = findViewById(R.id.support);
        accountstate = findViewById(R.id.WTextview);
        tsv_dollar = findViewById(R.id.tsv_dollar);
        e20cAccountState = findViewById(R.id.E20CTextview);
    }

    private void intEvent() {

        navigationHelper = new NavigationHelper(menu, action_bar, this);
        buy.setOnClickListener(view -> {
            // 创建意图对象
            Intent intent = new Intent();
            intent.setClass(MainActivity.this, BuyActivity.class);
            // 跳转
            startActivity(intent);
        });

        send.setOnClickListener(view -> {
            // 创建意图对象
            Intent intent = new Intent();
            intent.setClass(MainActivity.this, SendActivity.class);
            // 跳转
            startActivity(intent);
        });

        swap.setOnClickListener(view -> {
            // 创建意图对象
            Intent intent = new Intent();
            intent.setClass(MainActivity.this, SwapActivity.class);
            // 跳转
            startActivity(intent);
        });

        broker.setOnClickListener(view -> {
            // 创建意图对象
            Intent intent = new Intent();
            intent.setClass(MainActivity.this, BrokerActivity.class);
            // 跳转
            startActivity(intent);
        });

    }

    private void fetchAccountStatus() {
        // 获取保存的账户账号，假设是从 SharedPreferences 中获取
        String accountNumber = getAccountNumberFromSharedPreferences();
        if (accountNumber == null) {
            // 如果没有账户信息，可以给出提示或者默认值
            runOnUiThread(() -> {
                Toast.makeText(MainActivity.this, "未找到账户信息", Toast.LENGTH_LONG).show();
                updateAccountStatusText("0", "wBKC"); // 默认显示 0
                updateAccountStatusText("0", "E20C"); // 默认显示 0
            });
            return;
        }

        // 获取 wBKC 余额
        OkhttpUtils.getInstance().doGet(BaseUrl.QUERY_ACCOUNT_STATE_URL + "?addr=" + accountNumber + "&type=wBKC",
                new MyCallBack() {
                    @Override
                    public void onSuccess(String result) {
                        Log.d("wBKC_result:", result);
                        if (result == null || result.isEmpty()) {
                            updateAccountStatusText("0", "wBKC");
                        } else {
                            try {
                                JSONObject jsonResponse = new JSONObject(result);
                                String balance = jsonResponse.optString("balance", "0"); // 提供默认值以防 "balance" 字段不存在
                                Log.d("wBKC_balance:", balance);
                                updateAccountStatusText(balance, "wBKC");
                            } catch (JSONException e) {
                                e.printStackTrace();
                                updateAccountStatusText("0", "wBKC"); // 解析错误时显示 0
                                runOnUiThread(() -> Toast.makeText(MainActivity.this, "wBKC余额解析错误", Toast.LENGTH_SHORT)
                                        .show());
                            }
                        }
                    }

                    @Override
                    public Void onError(Exception e) {
                        runOnUiThread(() -> Toast.makeText(MainActivity.this, "获取wBKC余额网络出错", Toast.LENGTH_LONG).show());
                        updateAccountStatusText("0", "wBKC"); // 网络错误时显示 0
                        return null;
                    }
                });

        // 获取 E20C 余额
        OkhttpUtils.getInstance().doGet(BaseUrl.QUERY_ACCOUNT_STATE_URL + "?addr=" + accountNumber + "&type=E20C",
                new MyCallBack() {
                    @Override
                    public void onSuccess(String result) {
                        Log.d("E20C_result:", result);
                        if (result == null || result.isEmpty()) {
                            updateAccountStatusText("0", "E20C");
                        } else {
                            try {
                                JSONObject jsonResponse = new JSONObject(result);
                                String balance = jsonResponse.optString("balance", "0"); // 提供默认值
                                Log.d("E20C_balance:", balance);
                                updateAccountStatusText(balance, "E20C");
                            } catch (JSONException e) {
                                e.printStackTrace();
                                updateAccountStatusText("0", "E20C"); // 解析错误时显示 0
                                runOnUiThread(() -> Toast.makeText(MainActivity.this, "E20C余额解析错误", Toast.LENGTH_SHORT)
                                        .show());
                            }
                        }
                    }

                    @Override
                    public Void onError(Exception e) {
                        runOnUiThread(
                                () -> Toast.makeText(MainActivity.this, "获取E20C余额网络出错", Toast.LENGTH_LONG).show());
                        updateAccountStatusText("0", "E20C"); // 网络错误时显示 0
                        return null;
                    }
                });
    }

    private void updateAccountStatusText(final String balance, final String type) {
        // 在 UI 线程更新账户状态 TextView
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    double balanceValue = Double.parseDouble(balance); // 将余额转换为double
                    if ("wBKC".equals(type)) {
                        accountstate.setText(String.format("%.2f wBKC", balanceValue)); // 格式化输出，保留两位小数
                        tsv_dollar.setText(String.format("$%.2f USD", balanceValue / 10.0)); // wBKC 美元价值
                    } else if ("E20C".equals(type)) {
                        e20cAccountState.setText(String.format("%.2f E20C", balanceValue)); // 格式化输出
                        // 不再更新 E20C 的美元价值显示
                    }
                } catch (NumberFormatException e) {
                    // 处理余额不是有效数字的情况
                    Log.e("UpdateStatusText", "Invalid balance format: " + balance);
                    if ("wBKC".equals(type)) {
                        accountstate.setText("无效余额 wBKC");
                        tsv_dollar.setText("$0.00 USD");
                    } else if ("E20C".equals(type)) {
                        e20cAccountState.setText("无效余额 E20C");
                    }
                }
            }
        });
    }

    // 假设从 SharedPreferences 中获取账户账号的方法
    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
        // return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        IntentResult intentResult = IntentIntegrator.parseActivityResult(
                requestCode, resultCode, data);
        if (intentResult.getContents() != null) {
            String scannedData = intentResult.getContents();
            Intent intent = new Intent(this, SendActivity.class);
            intent.putExtra("scannedData", scannedData);
            startActivity(intent);

        }
    }

    @Override
    public void onBackPressed() {
        new AlertDialog.Builder(this)
                .setMessage("你确定要退出应用吗？")
                .setCancelable(false)
                .setPositiveButton("是", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int id) {
                        finishAffinity(); // 用户点击了确定按钮，结束所有Activity
                    }
                })
                .setNegativeButton("否", null)
                .show();
    }
}