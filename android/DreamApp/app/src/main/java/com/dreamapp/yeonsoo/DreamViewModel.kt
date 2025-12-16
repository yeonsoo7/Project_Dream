package com.dreamapp.yeonsoo

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class DreamViewModel : ViewModel() {
    private val _dreamText = MutableLiveData<String>()
    val dreamText: LiveData<String> get() = _dreamText
    val imageUrl  = MutableLiveData<String?>()

    fun setDreamText(text: String) { _dreamText.value = text }
    fun setImageUrl(url: String?) { imageUrl.value = url }
    fun clearImageUrl() { imageUrl.value = null }

    // 캘린더 부분
    private val _calendarDays = MutableStateFlow<List<CalendarDayEmotion>>(emptyList())
    val calendarDays: StateFlow<List<CalendarDayEmotion>> = _calendarDays

    private val _selectedDayDreams = MutableStateFlow<List<DreamDetail>>(emptyList())
    val selectedDayDreams: StateFlow<List<DreamDetail>> = _selectedDayDreams

    private val api = RetrofitClient.dreamCalendarApi

    fun loadCalendar(userId: String, month: String) {
        viewModelScope.launch {
            try {
                val days = api.getCalendar(userId, month)
                _calendarDays.value = days
            } catch (e: Exception) {
                e.printStackTrace()
                _calendarDays.value = emptyList()
            }
        }
    }

    fun loadDreamsByDate(userId: String, date: String) {
        viewModelScope.launch {
            try {
                val dreams = api.getDreamsByDate(userId, date)
                _selectedDayDreams.value = dreams
            } catch (e: Exception) {
                e.printStackTrace()
                _selectedDayDreams.value = emptyList()
            }
        }
    }

}
