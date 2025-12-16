package com.dreamapp.yeonsoo

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    private const val BASE_URL = "http://10.0.2.2:8000/" // 에뮬레이터
//    private const val BASE_URL = "http://192.168.0.5:8000/" // 휴대폰 테스트 시

    private val logger = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val http: OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(logger)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS)     // DALL·E 생성/다운로드 대비
        .writeTimeout(180, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)                      // 반드시 '/'로 끝나야 함
        .client(http)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    // 🎙 STT
    val api: SttApi by lazy { retrofit.create(SttApi::class.java) }

    // 🖼 이미지
    val imageApi: ImageApi by lazy { retrofit.create(ImageApi::class.java) }

    // 꿈 분석
    val dreamAnalysisApi: DreamAnalysisApi by lazy {
        retrofit.create(DreamAnalysisApi::class.java)
    }

    // 꿈 캘린더
    val dreamCalendarApi: DreamCalendarApi = retrofit.create(DreamCalendarApi::class.java)


    fun <T> create(service: Class<T>): T = retrofit.create(service)
}
