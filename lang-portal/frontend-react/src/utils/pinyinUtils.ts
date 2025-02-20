// Jiantizi adaption for Bootcamp Week 1:
// Add utilities for handling pinyin tone marks

const pinyinTonesMap = {
  'a': ['a', 'ā', 'á', 'ǎ', 'à'],
  'e': ['e', 'ē', 'é', 'ě', 'è'],
  'i': ['i', 'ī', 'í', 'ǐ', 'ì'],
  'o': ['o', 'ō', 'ó', 'ǒ', 'ò'],
  'u': ['u', 'ū', 'ú', 'ǔ', 'ù'],
  'ü': ['ü', 'ǖ', 'ǘ', 'ǚ', 'ǜ']
};

export function addToneMarks(pinyin: string, tone: number): string {
  if (tone < 1 || tone > 4) return pinyin;
  
  // Find the vowel to modify
  const vowels = 'aeiouü';
  let vowelIndex = -1;
  
  // Special cases for multiple vowels
  if (pinyin.includes('iu')) {
    vowelIndex = pinyin.indexOf('u');
  } else if (pinyin.includes('ui')) {
    vowelIndex = pinyin.indexOf('i');
  } else if (pinyin.includes('ian')) {
    vowelIndex = pinyin.indexOf('a');
  } else if (pinyin.includes('ia')) {
    vowelIndex = pinyin.indexOf('a');
  } else if (pinyin.includes('ao')) {
    vowelIndex = pinyin.indexOf('a');
  } else if (pinyin.includes('ai')) {
    vowelIndex = pinyin.indexOf('a');
  } else {
    // Find the first vowel
    for (let i = 0; i < pinyin.length; i++) {
      if (vowels.includes(pinyin[i].toLowerCase())) {
        vowelIndex = i;
        break;
      }
    }
  }

  if (vowelIndex === -1) return pinyin;

  const vowel = pinyin[vowelIndex].toLowerCase();
  const toneChar = pinyinTonesMap[vowel as keyof typeof pinyinTonesMap][tone];
  
  return pinyin.slice(0, vowelIndex) + toneChar + pinyin.slice(vowelIndex + 1);
}

export function removeToneMarks(pinyin: string): string {
  let result = pinyin;
  for (const [base, tones] of Object.entries(pinyinTonesMap)) {
    for (const tone of tones) {
      result = result.replace(new RegExp(tone, 'g'), base);
    }
  }
  return result;
} 