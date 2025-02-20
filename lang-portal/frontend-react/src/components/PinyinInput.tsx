// Jiantizi adaption for Bootcamp Week 1:
// Add component for handling pinyin input with tone marks

import React, { useState, useEffect } from 'react';
import { addToneMarks } from '../utils/pinyinUtils';

interface PinyinInputProps {
  value?: string;
  onChange: (value: string) => void;
  className?: string;
}

export const PinyinInput: React.FC<PinyinInputProps> = ({ value = '', onChange, className = '' }) => {
  const [rawInput, setRawInput] = useState('');

  useEffect(() => {
    // Convert initial value if provided
    if (value) {
      setRawInput(value);
    }
  }, [value]);

  const handleInput = (input: string) => {
    setRawInput(input);
    
    // Convert numbered pinyin to tone marks
    // e.g., "ni3" becomes "nǐ"
    const parts = input.split(' ');
    const withTones = parts.map(part => {
      const tone = parseInt(part.slice(-1));
      if (isNaN(tone) || tone < 1 || tone > 4) return part;
      return addToneMarks(part.slice(0, -1), tone);
    }).join(' ');
    
    onChange(withTones);
  };

  return (
    <input
      type="text"
      value={rawInput}
      onChange={(e) => handleInput(e.target.value)}
      className={`pinyin-input ${className}`}
      placeholder="Enter pinyin with numbers (e.g., ni3 hao3)"
    />
  );
}; 