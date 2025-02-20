import React from 'react';

interface ChineseWordProps {
  jiantizi: string;
  pinyin: string;
  english?: string;
  className?: string;
}

export const ChineseWord: React.FC<ChineseWordProps> = ({
  jiantizi,
  pinyin,
  english,
  className = ''
}) => {
  return (
    <div className={`chinese-word ${className}`}>
      <div className="chinese-character">{jiantizi}</div>
      <div className="pinyin">{pinyin}</div>
      {english && <div className="english">{english}</div>}
    </div>
  );
}; 