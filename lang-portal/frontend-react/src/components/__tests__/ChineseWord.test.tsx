// Jiantizi adaption for Bootcamp Week 1:
// Add tests for Chinese word display component

import { render } from '@testing-library/react';
import { ChineseWord } from '../ChineseWord';

describe('ChineseWord', () => {
  test('renders Chinese characters and pinyin', () => {
    const { getByText } = render(
      <ChineseWord jiantizi="学习" pinyin="xué xí" />
    );

    expect(getByText('学习')).toHaveClass('chinese-character');
    expect(getByText('xué xí')).toHaveClass('pinyin');
  });

  test('renders optional English translation', () => {
    const { getByText } = render(
      <ChineseWord 
        jiantizi="学习" 
        pinyin="xué xí" 
        english="to study" 
      />
    );

    expect(getByText('to study')).toHaveClass('english');
  });

  test('applies custom className', () => {
    const { container } = render(
      <ChineseWord 
        jiantizi="学习" 
        pinyin="xué xí" 
        className="custom-class" 
      />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
}); 