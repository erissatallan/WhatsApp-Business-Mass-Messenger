import React from 'react';

const Footer = () => {
  return (
    <footer className="mt-12 py-6 border-t border-gray-200 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center">
          <p className="text-gray-600" style={{fontSize: '10px'}}>
            By <span className="font-medium text-gray-900">Erissat Allan</span>
            {' '}
            <span>254759469851</span>
            {' '}
            <a 
              href="mailto:aerissat@gmail.com" 
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              aerissat@gmail.com
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
