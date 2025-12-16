package com.dreamapp.yeonsoo

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class DreamDetailAdapter(
    private var items: List<DreamDetail>
) : RecyclerView.Adapter<DreamDetailAdapter.DreamViewHolder>() {

    class DreamViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val tvDreamText: TextView = itemView.findViewById(R.id.tvDreamText)
        val tvValence: TextView = itemView.findViewById(R.id.tvValence)
        val tvNote: TextView = itemView.findViewById(R.id.tvNote)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DreamViewHolder {
        val v = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_dream_detail, parent, false)
        return DreamViewHolder(v)
    }

    override fun onBindViewHolder(holder: DreamViewHolder, position: Int) {
        val item = items[position]
        holder.tvDreamText.text = item.text

        val pos = item.valence["positive"] ?: 0.5
        val neg = item.valence["negative"] ?: 0.5
        holder.tvValence.text = String.format("긍/부정: P=%.2f / N=%.2f", pos, neg)

        val firstNote = item.nlg_notes.firstOrNull() ?: "요약 노트 없음"
        holder.tvNote.text = firstNote
    }

    override fun getItemCount(): Int = items.size

    fun submitList(newItems: List<DreamDetail>) {
        items = newItems
        notifyDataSetChanged()
    }
}
