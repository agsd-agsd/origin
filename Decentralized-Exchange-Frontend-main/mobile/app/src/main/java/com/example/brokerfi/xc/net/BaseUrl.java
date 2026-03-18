package com.example.brokerfi.xc.net;

public class BaseUrl {

    // Android 模拟器访问电脑 localhost 的特殊 IP: 10.0.2.2
    // 端口号 8545 对应 BrokerHub开启的端口
    public static String Base = "http://10.0.2.2:8545/broker-fi/";
    
//    public static String Base = "http://172.27.10.47:8082/broker-fi/";
//    public static String Base = "http://172.16.108.106:51732/broker-fi/";
//    public static String Base = "http://1d4928a8.r7.cpolar.top/broker-fi/";
//    public static  String REQUEST_URL="http://730a1bdb.r28.cpolar.top/broker-fi/query";
    public static  String QUERY_ACCOUNT_STATE_URL =Base+"query-g";
//    public static  String REQUEST_URL="https://61843335.r2.cpolar.top/broker-fi/query-g";
    public static String SEND_TX_URL =Base+"sendTxtoB2E";
//    public static String POST_URL="https://61843335.r2.cpolar.top/broker-fi/sendtx";

    public static String ApplyBrokerURL =Base+ "applybroker";
    public static String QueryBrokerProfitURL = Base+"querybrokerprofit";
    public static String QueryIsBrokerURL =Base+ "queryisbroker";
    public static String BecomeBrokerURL =Base+ "BecomeBrokerOrStakeMore";
    public static String WithdrawBrokerURL =Base+ "withdrawbroker";

    // 新增的 SWAP_URL
    public static String SWAP_URL = Base + "exchange";

}
