package com.example.brokerfi.xc;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.util.Log;
import android.util.TypedValue;
import android.view.View;
import android.view.ViewTreeObserver;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.example.brokerfi.R;
import com.example.brokerfi.xc.menu.NavigationHelper;
import com.example.brokerfi.xc.net.BaseUrl;
import com.example.brokerfi.xc.net.MyCallBack;
import com.example.brokerfi.xc.net.OkhttpUtils;
import com.example.brokerfi.xc.tool.UnitConverter;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

import org.json.JSONException;
import org.json.JSONObject;

import java.text.DecimalFormat;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import okhttp3.Request;

public class AfterBrokerActivity extends AppCompatActivity {
    private ImageView menu;
    private RelativeLayout action_bar;
    private ImageView buy;
    private ImageView send;
    private ImageView swap;
    private ImageView broker;
    private LinearLayout support;
    private Button btn_stake;
    private Button btn_withdraw;
    private LinearLayout brokerprofit;
    private NavigationHelper navigationHelper;
    private TextView wbkctextview;
    private TextView wbkcprofittextview;
    private TextView dollartextview;
    boolean hasExecuted_btn1 = false;// 保证按钮1只被初始化一次
    boolean hasExecuted_btn2 = false;// 保证按钮2只被初始化一次

    private volatile boolean flag = false;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_after_broker);
        intView();
        intEvent();

        new Thread(()->{

            while (true){
                if(flag){
                    break;
                }
                CountDownLatch latch = new CountDownLatch(1);
                initbrokerprofitview(latch);

                try {
                    latch.await(3000, TimeUnit.SECONDS);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                try {
                    Thread.sleep(500L);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }

            }

        }).start();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        flag=true;
    }

    private void initbrokerprofitview(CountDownLatch latch){

//        String accountNumber = getAccountNumberFromSharedPreferences();
//        OkhttpUtils.getInstance().doGet(BaseUrl.REQUEST_URL + "?addr=" + accountNumber, new MyCallBack() {
//            @Override
//            public void onSuccess(String result)  {
//                Log.d("result:", result);
//
//
//                    // 解析返回的 JSON 数据
//                    JSONObject jsonResponse = null;
//                    try {
//                        jsonResponse = new JSONObject(result);
//                    } catch (JSONException e) {
//                        e.printStackTrace();
//
//                    }
////                Log.d("jsonResponse:", String.valueOf(jsonResponse));
//
//                    // 获取 balance 字段的内容
//                    String balance = jsonResponse.optString("balance");
//
//                runOnUiThread(new Runnable() {
//                    @Override
//                    public void run() {
//                        wbkctextview.setText(balance+" wBKC");
//                        dollartextview.setText("$"+ (Double.parseDouble(balance) / 10) +"USD");
//                    }
//                });
//
//
//            }
//
//            @Override
//            public Void onError(Exception e) {
//                Toast.makeText(AfterBrokerActivity.this,"网络出错",Toast.LENGTH_LONG).show();
//
//                return null;
//            }
//        });

        OkhttpUtils.getInstance().doGet(BaseUrl.QueryBrokerProfitURL + "?addr=" + getAccountNumberFromSharedPreferences(), new MyCallBack() {
            @Override
            public void onSuccess(String result)  {
                Log.d("result:", result);
                if(result==""){
                    
                }else{
                    // 解析返回的 JSON 数据
                    JSONObject jsonResponse = null;
                    try {
                        jsonResponse = new JSONObject(result);
                        Double max = 0.0;
                        Double sum = 0.0;
                        Double sumBalance = 0.0;
                        for (int i = 0; i < 10000; i++) {
                            String s;
                            try {
                                 s= jsonResponse.getString(String.valueOf(i));
                                if ( s == null ){
                                    break;
                                }
                            }catch (Exception e){
                                break;
                            }
                            String[] split = s.split("/");
                            sum += Double.parseDouble(split[0]);
                            sumBalance+=Double.parseDouble(split[1]);
//                            max=Math.max(max,Double.parseDouble(s[0]));
                        }

                        Double finalSum = sum;
                        Double finalSumBalance = sumBalance;
                        JSONObject finalJsonResponse = jsonResponse;
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                wbkcprofittextview.setText("+"+ (int)(finalSum.intValue()) +" wBKC");
                                wbkctextview.setText(finalSumBalance +" wBKC");
                                double usd = finalSumBalance / (double)10;
                                DecimalFormat df = new DecimalFormat("#.0");
                                String formattedUsd = df.format(usd);
                                dollartextview.setText("$"+ formattedUsd +"USD");
                                brokerprofit.removeAllViews();

                                for (int i = 0; i < 10000; i++) {
                                    String s;
                                    try {
                                        s= finalJsonResponse.getString(String.valueOf(i));
                                        if ( s == null ){
                                            break;
                                        }
                                    }catch (Exception e){
                                        break;
                                    }

                                    String[] split = s.split("/");


                                    RelativeLayout relativeLayout = new RelativeLayout(AfterBrokerActivity.this);
                                    RelativeLayout.LayoutParams layoutParams = new RelativeLayout.LayoutParams(
                                            RelativeLayout.LayoutParams.MATCH_PARENT,
                                            RelativeLayout.LayoutParams.WRAP_CONTENT
                                    );
                                    relativeLayout.setLayoutParams(layoutParams);

                                    TextView shardTextView = new TextView(AfterBrokerActivity.this);
                                    shardTextView.setText("SHARD " + i);
                                    shardTextView.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 14);
                                    shardTextView.setTextColor(ContextCompat.getColor(AfterBrokerActivity.this, R.color.white));
                                    RelativeLayout.LayoutParams shardParams = new RelativeLayout.LayoutParams(
                                            RelativeLayout.LayoutParams.WRAP_CONTENT,
                                            RelativeLayout.LayoutParams.WRAP_CONTENT
                                    );
                                    shardParams.addRule(RelativeLayout.ALIGN_PARENT_LEFT);
                                    shardTextView.setLayoutParams(shardParams);
                                    relativeLayout.addView(shardTextView);


                                    TextView shardTextView2 = new TextView(AfterBrokerActivity.this);
                                    shardTextView2.setText(s);
                                    shardTextView2.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 14);
                                    shardTextView2.setTextColor(ContextCompat.getColor(AfterBrokerActivity.this, R.color.white));
                                    RelativeLayout.LayoutParams shardParams2 = new RelativeLayout.LayoutParams(
                                            RelativeLayout.LayoutParams.WRAP_CONTENT,
                                            RelativeLayout.LayoutParams.WRAP_CONTENT
                                    );
                                    shardParams2.addRule(RelativeLayout.ALIGN_PARENT_RIGHT);
                                    shardTextView2.setLayoutParams(shardParams2);
                                    relativeLayout.addView(shardTextView2);

                                    brokerprofit.addView(relativeLayout);

                                    ProgressBar progressBar = new ProgressBar(AfterBrokerActivity.this,null, android.R.attr.progressBarStyleHorizontal);
                                    progressBar.setLayoutParams(new LinearLayout.LayoutParams(
                                            LinearLayout.LayoutParams.MATCH_PARENT,
                                            (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 8, getResources().getDisplayMetrics())
                                    ));

                                    progressBar.setProgressDrawable(ContextCompat.getDrawable(AfterBrokerActivity.this,R.drawable.layer_list_progress_drawable));
                                    progressBar.setBackgroundColor(Color.WHITE); // 注意：这里设置背景色可能不会有效果，因为 progressDrawable 会覆盖它
//                            progressBar.setMax(max.intValue());
                                    progressBar.setMax((int)Double.parseDouble(split[1]));
                                    progressBar.setProgress((int )Double.parseDouble(split[0]));
                                    progressBar.setProgressTintList(ColorStateList.valueOf(ContextCompat.getColor(AfterBrokerActivity.this, R.color.green)));
                                    progressBar.setSecondaryProgressTintList(ColorStateList.valueOf(ContextCompat.getColor(AfterBrokerActivity.this, R.color.grey)));
                                    brokerprofit.addView(progressBar);

                                }
                            }
                        });

                        
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    

                }

                latch.countDown();
            }

            @Override
            public Void onError(Exception e) {
                Toast.makeText(AfterBrokerActivity.this,"网络出错",Toast.LENGTH_LONG).show();

                latch.countDown();
                return null;
            }
        });


    }



    private void intView() {
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        buy = findViewById(R.id.buy);
        send = findViewById(R.id.send);
        swap = findViewById(R.id.swap);
        broker = findViewById(R.id.broker);
        support = findViewById(R.id.support);
        btn_stake = findViewById(R.id.btn_stake);
        btn_withdraw = findViewById(R.id.btn_withdraw);
        brokerprofit = findViewById(R.id.BrokerLinearLayout);

        wbkctextview = findViewById(R.id.wbkctextview);
        wbkcprofittextview = findViewById(R.id.wbkcprofittextview);
        dollartextview = findViewById(R.id.dollartextview);
    }
    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";
    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null); // 如果没有找到，返回null

        // 在这里编写从 SharedPreferences 中获取账户账号的逻辑
//        return "123456789"; // 这里是示例，你需要根据实际情况获取正确的账户账号
    }
    private void intEvent(){
        navigationHelper = new NavigationHelper(menu, action_bar,this);
        //设置按钮上面的图标和文字（因为在布局没有办法把图标放在中间）
        buttonWithIconAndText();
        buy.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(AfterBrokerActivity.this,BuyActivity.class);
            //跳转
            startActivity(intent);
        });

        send.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(AfterBrokerActivity.this,SendActivity.class);
            //跳转
            startActivity(intent);
        });

        swap.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(AfterBrokerActivity.this,SwapActivity.class);
            //跳转
            startActivity(intent);
        });

        broker.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(AfterBrokerActivity.this,BrokerActivity.class);
            //跳转
            startActivity(intent);
        });
        btn_stake.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(AfterBrokerActivity.this,StakeMoreActivity.class);
            //跳转
            startActivity(intent);
        });
        btn_withdraw.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(AfterBrokerActivity.this,WithdrawActivity.class);
            //跳转
            startActivity(intent);
        });

    }
    private void buttonWithIconAndText(){
        ViewTreeObserver vto_btn1 = btn_stake.getViewTreeObserver();
        vto_btn1.addOnGlobalLayoutListener(new ViewTreeObserver.OnGlobalLayoutListener() {
            @Override
            public void onGlobalLayout() {
                if(!hasExecuted_btn1){
                    btn_stake.getViewTreeObserver().removeOnGlobalLayoutListener(this);
                    hasExecuted_btn1 = true; // 设置标志为已执行
                    Drawable[] drawables = btn_stake.getCompoundDrawables();
                    Drawable leftDrawable = drawables[0]; // 获取左侧图标
                    String buttonText = btn_stake.getText().toString(); // 获取按钮文本
                    int totalWidth = 0;
                    if (leftDrawable != null) {
                        totalWidth += leftDrawable.getIntrinsicWidth();
                    }
                    totalWidth += (int) btn_stake.getPaint().measureText(buttonText);
                    int buttonWidth = btn_stake.getWidth();
                    int paddingLeft = (buttonWidth - totalWidth ) / 2;
                    btn_stake.setPadding(paddingLeft, btn_stake.getPaddingTop(), btn_stake.getPaddingRight(), btn_stake.getPaddingBottom());


                }

            }
        });
        ViewTreeObserver vto_btn2 = btn_withdraw.getViewTreeObserver();
        vto_btn2.addOnGlobalLayoutListener(new ViewTreeObserver.OnGlobalLayoutListener() {
            @Override
            public void onGlobalLayout() {
                if(!hasExecuted_btn2){
                    btn_withdraw.getViewTreeObserver().removeOnGlobalLayoutListener(this);
                    hasExecuted_btn2 = true; // 设置标志为已执行
                    Drawable[] drawables = btn_withdraw.getCompoundDrawables();
                    Drawable leftDrawable = drawables[0]; // 获取左侧图标
                    String buttonText = btn_withdraw.getText().toString(); // 获取按钮文本
                    int totalWidth = 0;
                    if (leftDrawable != null) {
                        totalWidth += leftDrawable.getIntrinsicWidth();
                    }
                    totalWidth += (int) btn_withdraw.getPaint().measureText(buttonText);
                    int buttonWidth = btn_withdraw.getWidth();
                    int paddingLeft = (buttonWidth - totalWidth) / 2;
                    btn_withdraw.setPadding(paddingLeft, btn_withdraw.getPaddingTop(), btn_withdraw.getPaddingRight(), btn_withdraw.getPaddingBottom());


                }

            }
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