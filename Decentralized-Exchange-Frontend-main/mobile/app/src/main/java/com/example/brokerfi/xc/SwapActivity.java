package com.example.brokerfi.xc;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.AppCompatButton;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.RelativeLayout; // Import RelativeLayout
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.example.brokerfi.R;
import com.example.brokerfi.xc.menu.NavigationHelper;
import com.example.brokerfi.xc.net.BaseUrl;
import com.example.brokerfi.xc.net.MyCallBack;
import com.example.brokerfi.xc.net.OkhttpUtils;

import org.json.JSONObject;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;

public class SwapActivity extends AppCompatActivity {

    private ImageView menuImageView;
    private NavigationHelper navigationHelper;
    private Spinner fromCurrencySpinner;
    private Spinner toCurrencySpinner;
    private EditText fromAmountEditText;
    private TextView toAmountTextView;
    private TextView exchangeRateTextView;
    private AppCompatButton swapButton;
    private ProgressBar progressBarSwap;

    private static final String PREFS_NAME = "MyPrefsFile";
    private static final String PREF_ACCOUNT_NUMBER = "accountNumber";

    private static final String CURRENCY_wBKC_KEY = "wBKC";
    private static final String CURRENCY_BADGE_KEY = "E20C";
    private static final String API_SUCCESS_CODE = "0";

    private final double simulatedExchangeRatewBKCToE20C = 10.0;
    private final double simulatedExchangeRateE20CTowBKC = 0.1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_swap);

        initViews();
        initEventListeners();
        initSpinners();
        checkAccountAndSetButtonState();
    }

    private void initViews() {
        menuImageView = findViewById(R.id.menu);
        fromCurrencySpinner = findViewById(R.id.from_currency_spinner);
        toCurrencySpinner = findViewById(R.id.to_currency_spinner);
        fromAmountEditText = findViewById(R.id.from_amount_edit_text);
        toAmountTextView = findViewById(R.id.to_amount_text_view);
        exchangeRateTextView = findViewById(R.id.exchange_rate_text_view);
        swapButton = findViewById(R.id.swap_button);
        progressBarSwap = findViewById(R.id.progressBarSwapLoading);
    }

    private void checkAccountAndSetButtonState() {
        if (getAccountNumberFromSharedPreferences() == null) {
            if (swapButton != null) {
                swapButton.setEnabled(false);
            }
            Toast.makeText(this, getString(R.string.swap_account_not_found_disabled), Toast.LENGTH_LONG).show();
        } else {
            if (swapButton != null) {
                swapButton.setEnabled(true);
            }
        }
    }

    private void initEventListeners() {
        View tempView = findViewById(R.id.action_bar);
        RelativeLayout actionBarLayout = null;

        if (tempView instanceof RelativeLayout) {
            actionBarLayout = (RelativeLayout) tempView;
        } else {
            if (tempView == null) {
                Log.e("SwapActivity", "ActionBar (R.id.action_bar) not found.");
            } else {
                Log.e("SwapActivity", "View with ID R.id.action_bar is not a RelativeLayout. Actual type: " + tempView.getClass().getName());
            }
        }

        if (menuImageView != null && actionBarLayout != null) {
            navigationHelper = new NavigationHelper(menuImageView, actionBarLayout, this);
        } else {
            if (menuImageView == null) Log.e("SwapActivity", "Menu ImageView (R.id.menu) not found.");
        }

        fromAmountEditText.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                calculateAndDisplayTargetAmount();
            }
            @Override
            public void afterTextChanged(Editable s) {}
        });

        AdapterView.OnItemSelectedListener spinnerListener = new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (fromCurrencySpinner.getSelectedItemPosition() == toCurrencySpinner.getSelectedItemPosition()) {
                    Toast.makeText(SwapActivity.this, getString(R.string.swap_error_same_currency), Toast.LENGTH_SHORT).show();
                }
                calculateAndDisplayTargetAmount();
                updateExchangeRateDisplay();
            }
            @Override
            public void onNothingSelected(AdapterView<?> parent) {}
        };

        fromCurrencySpinner.setOnItemSelectedListener(spinnerListener);
        toCurrencySpinner.setOnItemSelectedListener(spinnerListener);

        if (swapButton != null) {
            swapButton.setOnClickListener(v -> performSwap());
        }
    }

    private void initSpinners() {
        List<String> currenciesForLogic = Arrays.asList(CURRENCY_wBKC_KEY, CURRENCY_BADGE_KEY);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, currenciesForLogic);

        fromCurrencySpinner.setAdapter(adapter);
        toCurrencySpinner.setAdapter(adapter);

        if (currenciesForLogic.size() > 1) {
            toCurrencySpinner.setSelection(1);
        }
        calculateAndDisplayTargetAmount();
        updateExchangeRateDisplay();
    }

    private void updateExchangeRateDisplay() {
        if (fromCurrencySpinner.getSelectedItem() == null || toCurrencySpinner.getSelectedItem() == null) {
            exchangeRateTextView.setText(getString(R.string.swap_exchange_rate_unavailable));
            return;
        }
        String fromCurrencyKey = fromCurrencySpinner.getSelectedItem().toString();
        String toCurrencyKey = toCurrencySpinner.getSelectedItem().toString();

        if (fromCurrencyKey.equals(toCurrencyKey)) {
            exchangeRateTextView.setText(String.format(Locale.getDefault(), getString(R.string.swap_exchange_rate_format_same), fromCurrencyKey, toCurrencyKey));
        } else if (CURRENCY_wBKC_KEY.equals(fromCurrencyKey) && CURRENCY_BADGE_KEY.equals(toCurrencyKey)) {
            exchangeRateTextView.setText(String.format(Locale.getDefault(), getString(R.string.swap_exchange_rate_format_simulated), CURRENCY_wBKC_KEY, simulatedExchangeRatewBKCToE20C, CURRENCY_BADGE_KEY));
        } else if (CURRENCY_BADGE_KEY.equals(fromCurrencyKey) && CURRENCY_wBKC_KEY.equals(toCurrencyKey)) {
            exchangeRateTextView.setText(String.format(Locale.getDefault(), getString(R.string.swap_exchange_rate_format_simulated), CURRENCY_BADGE_KEY, simulatedExchangeRateE20CTowBKC, CURRENCY_wBKC_KEY));
        } else {
            exchangeRateTextView.setText(getString(R.string.swap_exchange_rate_unavailable));
        }
    }

    private void calculateAndDisplayTargetAmount() {
        if (fromCurrencySpinner.getSelectedItem() == null || toCurrencySpinner.getSelectedItem() == null || fromAmountEditText.getText() == null) {
            toAmountTextView.setText("");
            return;
        }
        String fromCurrencyKey = fromCurrencySpinner.getSelectedItem().toString();
        String toCurrencyKey = toCurrencySpinner.getSelectedItem().toString();
        String amountStr = fromAmountEditText.getText().toString();

        if (amountStr.isEmpty()) {
            toAmountTextView.setText("");
            return;
        }

        double rawAmount; // 用户可能输入小数
        try {
            rawAmount = Double.parseDouble(amountStr);
        } catch (NumberFormatException e) {
            toAmountTextView.setText("");
            return;
        }

        long amountToCalculate = (long) rawAmount; // MODIFIED: 使用整数部分进行计算和后续发送

        if (amountToCalculate < 0) { // 检查转换后的整数值
            toAmountTextView.setText(""); // 或者提示错误
            return;
        }

        if (fromCurrencyKey.equals(toCurrencyKey)) {
            // 如果货币相同，目标金额也应该是整数
            toAmountTextView.setText(String.format(Locale.getDefault(), "%d", amountToCalculate));
        } else if (CURRENCY_wBKC_KEY.equals(fromCurrencyKey) && CURRENCY_BADGE_KEY.equals(toCurrencyKey)) {
            // 目标金额的计算结果可以是小数，按原样显示
            toAmountTextView.setText(String.format(Locale.getDefault(), "%.2f", amountToCalculate * simulatedExchangeRatewBKCToE20C));
        } else if (CURRENCY_BADGE_KEY.equals(fromCurrencyKey) && CURRENCY_wBKC_KEY.equals(toCurrencyKey)) {
            toAmountTextView.setText(String.format(Locale.getDefault(), "%.2f", amountToCalculate * simulatedExchangeRateE20CTowBKC));
        } else {
            toAmountTextView.setText(getString(R.string.swap_amount_not_applicable));
        }
    }

    private void setInteractionEnabled(boolean enabled) {
        fromAmountEditText.setEnabled(enabled);
        fromCurrencySpinner.setEnabled(enabled);
        toCurrencySpinner.setEnabled(enabled);
        if (swapButton != null) swapButton.setEnabled(enabled);
        if (progressBarSwap != null) {
            progressBarSwap.setVisibility(enabled ? View.GONE : View.VISIBLE);
        }
    }

    private void performSwap() {
        Log.d("SwapActivity_Debug", "performSwap() 方法开始执行。");
        if (fromCurrencySpinner.getSelectedItem() == null ||
                toCurrencySpinner.getSelectedItem() == null ||
                fromAmountEditText.getText() == null) {
            Log.d("SwapActivity_Debug", "performSwap() 提前退出: Spinner或EditText为空。");
            Toast.makeText(this, getString(R.string.swap_error_invalid_amount), Toast.LENGTH_SHORT).show();
            return;
        }

        String fromCurrencyKey = fromCurrencySpinner.getSelectedItem().toString();
        String toCurrencyKey = toCurrencySpinner.getSelectedItem().toString();
        String amountStr = fromAmountEditText.getText().toString();

        Log.d("SwapActivity_Debug", "选择的 From Currency: " + fromCurrencyKey);
        Log.d("SwapActivity_Debug", "选择的 To Currency: " + toCurrencyKey);
        Log.d("SwapActivity_Debug", "输入的金额字符串: '" + amountStr + "'");


        if (fromCurrencyKey.equals(toCurrencyKey)) {
            Log.d("SwapActivity_Debug", "performSwap() 提前退出: fromCurrency 和 toCurrency 相同。");
            Toast.makeText(this, getString(R.string.swap_error_same_currency), Toast.LENGTH_SHORT).show();
            return;
        }

        if (amountStr.isEmpty()) {
            Log.d("SwapActivity_Debug", "performSwap() 提前退出: 金额字符串为空。");
            Toast.makeText(this, getString(R.string.swap_error_enter_amount), Toast.LENGTH_SHORT).show();
            return;
        }

        double rawAmount; // 用户可能输入小数
        try {
            rawAmount = Double.parseDouble(amountStr);
        } catch (NumberFormatException e) {
            Log.d("SwapActivity_Debug", "performSwap() 提前退出: 金额格式错误。", e);
            Toast.makeText(this, getString(R.string.swap_error_invalid_amount), Toast.LENGTH_SHORT).show();
            return;
        }

        long amountToSend = (long) rawAmount; // MODIFIED: 获取金额的整数部分用于发送
        Log.d("SwapActivity_Debug", "用于发送的整数金额: " + amountToSend);


        if (amountToSend <= 0) {
            Log.d("SwapActivity_Debug", "performSwap() 提前退出: 发送金额小于或等于0。");
            Toast.makeText(this, getString(R.string.swap_error_amount_not_positive), Toast.LENGTH_SHORT).show();
            return;
        }

        String accountNumber = getAccountNumberFromSharedPreferences();
        if (accountNumber == null) {
            Log.d("SwapActivity_Debug", "performSwap() 提前退出: 账户号码为null。");
            Toast.makeText(this, getString(R.string.swap_error_account_not_found), Toast.LENGTH_SHORT).show();
            if (swapButton != null) swapButton.setEnabled(false);
            return;
        }

        setInteractionEnabled(false);
        Toast.makeText(this, getString(R.string.swap_info_initiating), Toast.LENGTH_SHORT).show();

        // MODIFIED: 将整数金额转换为字符串发送
        String formattedAmount = String.format(Locale.US, "%d", amountToSend);
        Log.d("SwapActivity_Debug", "格式化后的发送金额 (token): " + formattedAmount);

        String swapUrl;
        if (CURRENCY_wBKC_KEY.equals(fromCurrencyKey) && CURRENCY_BADGE_KEY.equals(toCurrencyKey)) {
            // wBKC -> E20C: BecomeBrokerOrStakeMore
            swapUrl = BaseUrl.BecomeBrokerURL + "?addr=" + accountNumber + "&token=" + formattedAmount;
        } else if (CURRENCY_BADGE_KEY.equals(fromCurrencyKey) && CURRENCY_wBKC_KEY.equals(toCurrencyKey)) {
            // E20C -> wBKC: withdrawbroker
            swapUrl = BaseUrl.WithdrawBrokerURL + "?addr=" + accountNumber;
        } else {
             Toast.makeText(this, "Unsupport swap type", Toast.LENGTH_SHORT).show();
             setInteractionEnabled(true);
             return;
        }

        Log.d("SwapActivity_Request", "Swap URL: " + swapUrl); // 这个日志你之前看到了

        OkhttpUtils.getInstance().doGet(swapUrl, new MyCallBack() {
            @Override
            public void onSuccess(String result) {
                Log.d("SwapActivity_Response", "Swap Result: " + result); // 这个日志你也看到了
                runOnUiThread(() -> {
                    setInteractionEnabled(true);
                    try {
                        JSONObject jsonResponse = new JSONObject(result);

                        if (jsonResponse.has("msg") && "Done!".equals(jsonResponse.optString("msg"))) {
                            Toast.makeText(SwapActivity.this, getString(R.string.swap_success_message), Toast.LENGTH_LONG).show();
                            if (fromAmountEditText != null) {
                                fromAmountEditText.setText("");
                            }
                        } else if (jsonResponse.has("code") && API_SUCCESS_CODE.equals(jsonResponse.optString("code"))) {
                            String successMessage = jsonResponse.optString("message", getString(R.string.swap_success_message));
                            Toast.makeText(SwapActivity.this, successMessage, Toast.LENGTH_LONG).show();
                            if (fromAmountEditText != null) {
                                fromAmountEditText.setText("");
                            }
                        } else {
                            String errorMessage = "";
                            if (jsonResponse.has("error")) { // 优先检查 "error" 字段
                                errorMessage = jsonResponse.optString("error");
                            } else if (jsonResponse.has("message")) {
                                errorMessage = jsonResponse.optString("message");
                            } else if (jsonResponse.has("msg")) {
                                errorMessage = jsonResponse.optString("msg");
                            }

                            if (errorMessage.isEmpty()) {
                                errorMessage = getString(R.string.swap_error_processing_response);
                            }
                            Toast.makeText(SwapActivity.this, String.format(getString(R.string.swap_failed_with_reason), errorMessage), Toast.LENGTH_LONG).show();
                        }
                    } catch (Exception e) {
                        Log.e("SwapActivity_ParseError", "Error parsing swap response: " + result, e);
                        Toast.makeText(SwapActivity.this, getString(R.string.swap_error_processing_response), Toast.LENGTH_LONG).show();
                    }
                });
            }

            @Override
            public Void onError(Exception e) {
                Log.e("SwapActivity_HttpError", "Swap HTTP request failed", e);
                runOnUiThread(() -> {
                    setInteractionEnabled(true);
                    Toast.makeText(SwapActivity.this, getString(R.string.swap_error_request_failed), Toast.LENGTH_LONG).show();
                });
                return null;
            }
        });
    }

    private String getAccountNumberFromSharedPreferences() {
        SharedPreferences settings = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        return settings.getString(PREF_ACCOUNT_NUMBER, null);
    }
}