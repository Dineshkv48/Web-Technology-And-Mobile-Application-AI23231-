package com.example.font_change;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.res.ResourcesCompat;

public class MainActivity extends AppCompatActivity {

    TextView sampleText;
    Button changeStyleButton;

    // Multiple colors
    int[] colors = {
            Color.RED,
            Color.BLUE,
            Color.GREEN,
            Color.MAGENTA,
            Color.CYAN,
            Color.parseColor("#FF5722")
    };

    int currentIndex = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        sampleText = findViewById(R.id.sampleText);
        changeStyleButton = findViewById(R.id.changeStyleButton);

        changeStyleButton.setOnClickListener(v -> {

            // Change color
            sampleText.setTextColor(colors[currentIndex]);

            // Apply font
            Typeface typeface = ResourcesCompat.getFont(this, R.font.roboto_regular);
            if (typeface != null) {
                sampleText.setTypeface(typeface, Typeface.BOLD);
            }

            Toast.makeText(this, "Color Changed!", Toast.LENGTH_SHORT).show();

            // Move to next color
            currentIndex++;

            // Reset index if exceeds
            if (currentIndex >= colors.length) {
                currentIndex = 0;
            }
        });
    }
}