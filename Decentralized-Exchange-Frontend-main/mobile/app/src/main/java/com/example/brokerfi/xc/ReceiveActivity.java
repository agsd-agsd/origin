package com.example.brokerfi.xc;

import static java.lang.Math.min;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import android.Manifest;

import android.content.ClipData;
import android.content.ClipDescription;
import android.content.ClipboardManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.media.MediaScannerConnection;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.View;
import android.view.ViewTreeObserver;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.Toast;


import com.example.brokerfi.R;
import com.example.brokerfi.xc.menu.NavigationHelper;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.MultiFormatWriter;
import com.google.zxing.WriterException;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;
import com.journeyapps.barcodescanner.BarcodeEncoder;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.concurrent.atomic.AtomicBoolean;

public class ReceiveActivity extends AppCompatActivity {
    private static final int REQUEST_CODE_SAVE_IMAGE = 1;
    private ImageView menu;
    private RelativeLayout action_bar;
    private EditText edittext;
    private ImageView imageView;
    private NavigationHelper navigationHelper;
    private Button copyaddress;
    private Button saveqrcodebtn;
    private int qrcode_height;
    boolean hasExecuted = false;// 保证二维码高度等信息只会被初始化一次
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
        setContentView(R.layout.activity_receive);

        intView();
        try {
            intEvent();
        }catch (Exception e){
            e.printStackTrace();
        }

    }

    private void intView() {
        menu = findViewById(R.id.menu);
        action_bar = findViewById(R.id.action_bar);
        edittext = findViewById(R.id.edittext);
        imageView = findViewById(R.id.imageView);
        copyaddress = findViewById(R.id.copyaddress);
        saveqrcodebtn = findViewById(R.id.saveqrcodebtn);
    }

    private void intEvent() throws WriterException {
        //导航栏
        navigationHelper = new NavigationHelper(menu, action_bar,this);
        // 获取二维码的高度
        ViewTreeObserver vto = imageView.getViewTreeObserver();
        vto.addOnGlobalLayoutListener(new ViewTreeObserver.OnGlobalLayoutListener() {
            @Override
            public void onGlobalLayout() {
                if(!hasExecuted){
                    imageView.getViewTreeObserver().removeOnGlobalLayoutListener(this);
//                    qrcode_height = (int)min(imageView.getHeight(),imageView.getWidth());
                    qrcode_height = (int)imageView.getWidth();
                    hasExecuted = true; // 设置标志为已执行
                    edittext.setText(getAccountNumberFromSharedPreferences());//获取高度之后再设置编辑框中的内容触发edittext的监听器
//                    edittext.setEnabled(false);
                }

            }
        });

//        String s = edittext.getText().toString().trim();
//        MultiFormatWriter writer = new MultiFormatWriter();
//        BitMatrix matrix = writer.encode(s, BarcodeFormat.QR_CODE,qrcode_height,qrcode_height);
//        BarcodeEncoder encoder = new BarcodeEncoder();
//        Bitmap bitmap = encoder.createBitmap(matrix);
//        imageView.setImageBitmap(bitmap);

        //监听输入是否有变化，有变化的话要更新二维码
        edittext.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {

            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {
                if(charSequence.length() == 42||charSequence.length() == 40){
                    String s = edittext.getText().toString().trim();
                    MultiFormatWriter writer = new MultiFormatWriter();
                    Log.d("height", String.valueOf(qrcode_height));

                    try {
                        BitMatrix matrix = writer.encode(s, BarcodeFormat.QR_CODE,qrcode_height,qrcode_height);
                        BarcodeEncoder encoder = new BarcodeEncoder();
                        Bitmap bitmap = encoder.createBitmap(matrix);
                        imageView.setImageBitmap(bitmap);

                    } catch (WriterException e) {
                        e.printStackTrace();
                    }
                }

            }

            @Override
            public void afterTextChanged(Editable editable) {

            }
        });


        copyaddress.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                String stringtocopy = edittext.getText().toString();
                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);

                // 创建一个ClipData.Item对象，它包含要复制的文本
                ClipData.Item item = new ClipData.Item(stringtocopy);

                // 创建一个ClipData对象，并为其指定一个标签（这个标签对于复制粘贴操作本身并不重要）
                ClipData clip = new ClipData((CharSequence)null, new String[]{ClipDescription.MIMETYPE_TEXT_PLAIN}, item);

                // 将ClipData对象放到剪切板上
                clipboard.setPrimaryClip(clip);

                // 可选：向用户显示一个Toast消息，确认文本已复制
                Toast.makeText(ReceiveActivity.this, "文本已复制到剪切板", Toast.LENGTH_SHORT).show();
            }
        });


        saveqrcodebtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                if (ContextCompat.checkSelfPermission(ReceiveActivity.this, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                    // 请求写入外部存储的权限
                    ActivityCompat.requestPermissions(ReceiveActivity.this, new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQUEST_CODE_SAVE_IMAGE);
                } else {
                    String s = edittext.getText().toString().trim();
                    MultiFormatWriter writer = new MultiFormatWriter();
                    BitMatrix matrix = null;
                    try {
                        matrix = writer.encode(s, BarcodeFormat.QR_CODE,qrcode_height,qrcode_height);
                    } catch (WriterException e) {
                        throw new RuntimeException(e);
                    }
                    BarcodeEncoder encoder = new BarcodeEncoder();
                    Bitmap bitmap = encoder.createBitmap(matrix);
                    // 已经有权限，直接保存图片
                    saveImageToGallery(bitmap);
                }
            }
        });




    }

    // 权限请求的回调
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CODE_SAVE_IMAGE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                String s = edittext.getText().toString().trim();
                MultiFormatWriter writer = new MultiFormatWriter();
                BitMatrix matrix = null;
                try {
                    matrix = writer.encode(s, BarcodeFormat.QR_CODE,qrcode_height,qrcode_height);
                } catch (WriterException e) {
                    throw new RuntimeException(e);
                }
                BarcodeEncoder encoder = new BarcodeEncoder();
                Bitmap bitmap = encoder.createBitmap(matrix);
                // 权限被授予，保存图片
                saveImageToGallery(bitmap);
            } else {
                // 权限被拒绝，向用户显示消息
                Toast.makeText(ReceiveActivity.this, "需要存储权限来保存图片", Toast.LENGTH_SHORT).show();
            }
        }
    }

    // 保存图片到相册的方法
    private void saveImageToGallery(Bitmap bitmap) {
        // 注意：以下代码是简化的，并且可能需要根据您的具体需求进行调整
        // 例如，您可能需要为图片创建一个唯一的名称，并处理不同的Android版本差异
        File file = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "saved_image.png");
        try (FileOutputStream out = new FileOutputStream(file)) {
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, out); // 压缩图片并写入文件
            out.flush();

            // 通知媒体存储（Android 10及以上版本需要特别注意）
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                ContentValues values = new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME, "saved_image.png");
                values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
                values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/" + getPackageName());
                values.put(MediaStore.Images.Media.IS_PENDING, true);

                ContentResolver resolver = getContentResolver();
                Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);

                if (uri != null) {
                    try (OutputStream outputStream = resolver.openOutputStream(uri)) {
                        if (outputStream != null) {
                            bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream); // 再次压缩图片并写入MediaStore提供的URI
                            outputStream.flush();
                        }
                    } catch (IOException e) {
                        e.printStackTrace();
                    } finally {
                        values.clear();
                        values.put(MediaStore.Images.Media.IS_PENDING, false);
                        resolver.update(uri, values, null, null);
                    }
                }
            } else {
                // 对于Android 10以下的版本，上面的文件写入通常就足够了，因为系统会扫描新文件并添加到媒体库中
                // 但是，您也可以使用MediaScannerConnection来手动通知媒体存储
                MediaScannerConnection.scanFile(this, new String[]{file.getAbsolutePath()}, null, new MediaScannerConnection.OnScanCompletedListener() {
                    @Override
                    public void onScanCompleted(String path, Uri uri) {
                        // 图片已添加到媒体库
                    }
                });
            }

            // 可选：向用户显示Toast消息，确认图片已保存
            Toast.makeText(ReceiveActivity.this, "图片已保存到相册", Toast.LENGTH_SHORT).show();
        } catch (IOException e) {
            e.printStackTrace();
            // 处理文件写入错误
        }
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