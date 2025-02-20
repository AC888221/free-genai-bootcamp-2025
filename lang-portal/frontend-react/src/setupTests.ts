// Jiantizi adaption for Bootcamp Week 1:
// Configure test environment

import '@testing-library/jest-dom';
import '@testing-library/jest-dom/extend-expect';
import { configure } from '@testing-library/react';
import { act } from 'react';
import { act as domAct } from 'react-dom/test-utils';

// Configure testing library
configure({ 
  asyncUtilTimeout: 5000,
  testIdAttribute: 'data-testid'
});

// Declare global types
declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace NodeJS {
    interface Global {
      act: typeof act;
      domAct: typeof domAct;
    }
  }

  interface Window {
    act: typeof act;
    domAct: typeof domAct;
  }

  namespace jest {
    interface Matchers<R> {
      toHaveClass: (className: string) => R;
      toBeInTheDocument: () => R;
    }
  }
}

// Add act functions to global scope
(global as any).act = act;
(global as any).domAct = domAct; 