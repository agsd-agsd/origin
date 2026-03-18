package com.example.brokerfi.xc;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.TextView;

import com.example.brokerfi.R;
import com.example.brokerfi.xc.menu.NavigationHelper;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

public class SelectAccountActivity extends AppCompatActivity {
    private ImageView menu;
    private RelativeLayout action_bar;
    private Button btn_add;
    private NavigationHelper navigationHelper;
    private RelativeLayout currentLayout = null;
    private ImageView currentcheck ;
    private RelativeLayout.LayoutParams layoutParams;




    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_select_account);

        intView();
        intEvent();


    }

    private void intView() {
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        btn_add = findViewById(R.id.btn_add);
//        currentcheck = new ImageView(SelectAccountActivity.this);
        //初始化param
        layoutParams = new RelativeLayout.LayoutParams(
                RelativeLayout.LayoutParams.WRAP_CONTENT,
                RelativeLayout.LayoutParams.WRAP_CONTENT
        );

        layoutParams.addRule(RelativeLayout.ALIGN_PARENT_RIGHT,RelativeLayout.TRUE); // 设置在 sendicon 右侧
        layoutParams.addRule(RelativeLayout.CENTER_VERTICAL, RelativeLayout.TRUE); // 设置垂直居中

    }

    private void intEvent(){
        navigationHelper = new NavigationHelper(menu, action_bar,this);

        btn_add.setOnClickListener(view -> {
            //创建意图对象
            Intent intent = new Intent();
            intent.setClass(SelectAccountActivity.this, AddAccountActivity.class);
            //跳转
            startActivity(intent);
        });
    }
    public void onRelativeLayoutClick(View view) {
        RelativeLayout relativeLayout = (RelativeLayout) view;

        if (currentLayout != null) {
            int childCount = currentLayout.getChildCount();
            // 恢复上一个布局的默认状态
            currentLayout.setBackgroundColor(Color.WHITE);
            TextView textView=(TextView) currentLayout.getChildAt(childCount - 2);
            currentLayout.removeView(currentcheck);
            RelativeLayout.LayoutParams params=(RelativeLayout.LayoutParams) textView.getLayoutParams();
            params.removeRule(RelativeLayout.LEFT_OF);
            params.setMargins(0, 0, 0, 0);
            params.addRule(RelativeLayout.ALIGN_PARENT_RIGHT);
            textView.setLayoutParams(params);
            if(currentLayout == relativeLayout){
                currentLayout = null;
            }else{
                // 切换当前布局的背景
                int grayColor = Color.rgb(229, 231, 235);
                relativeLayout.setBackgroundColor(grayColor); // 这里的 selected_background 是一个资源文件，可以是你自定义的选中状态背景
                currentLayout = relativeLayout; // 更新当前被选中的布局
                TextView textView2 = (TextView) getLastView(relativeLayout);
                // 创建并添加新的 ImageView
                ImageView imageView = new ImageView(SelectAccountActivity.this);
                // 设置自定义的图片内容
                imageView.setImageResource(R.drawable.check);
                imageView.setId(View.generateViewId());//生成唯一的ID
                currentcheck=imageView;
                // 设置 ImageView 的布局参数
                imageView.setLayoutParams(layoutParams);
                // 将 ImageView 添加到当前被点击的 RelativeLayout 上
                relativeLayout.addView(imageView);
                RelativeLayout.LayoutParams params2=(RelativeLayout.LayoutParams) textView2.getLayoutParams();
                params2.addRule(RelativeLayout.LEFT_OF,imageView.getId());
                params2.setMargins(0, 0, 8, 0);
                params2.removeRule(RelativeLayout.ALIGN_PARENT_RIGHT);
                textView2.setLayoutParams(params2);

            }

        }else{
            // 切换当前布局的背景
            int grayColor = Color.rgb(229, 231, 235);
            relativeLayout.setBackgroundColor(grayColor); // 这里的 selected_background 是一个资源文件，可以是你自定义的选中状态背景
            currentLayout = relativeLayout; // 更新当前被选中的布局
            TextView textView = (TextView) getLastView(relativeLayout);
            // 创建并添加新的 ImageView
            ImageView imageView = new ImageView(SelectAccountActivity.this);
            // 设置自定义的图片内容
            imageView.setImageResource(R.drawable.check);
            imageView.setId(View.generateViewId());//生成唯一的ID
            currentcheck=imageView;
            // 设置 ImageView 的布局参数
            imageView.setLayoutParams(layoutParams);
            // 将 ImageView 添加到当前被点击的 RelativeLayout 上
            relativeLayout.addView(imageView);
            RelativeLayout.LayoutParams params=(RelativeLayout.LayoutParams) textView.getLayoutParams();
            params.addRule(RelativeLayout.LEFT_OF,imageView.getId());
            params.setMargins(0, 0, 8, 0);
            params.removeRule(RelativeLayout.ALIGN_PARENT_RIGHT);
            textView.setLayoutParams(params);

        }

    }
    // 寻找最后一个子视图
    private View getLastView(ViewGroup viewGroup) {
        int childCount = viewGroup.getChildCount();
        if (childCount > 0) {
            return viewGroup.getChildAt(childCount - 1);
        }
        return null;
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