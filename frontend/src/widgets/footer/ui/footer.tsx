import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#1f385c] dark:bg-slate-950 text-white mt-16 pt-12 pb-8 border-t border-slate-800 dark:border-slate-900 transition-colors">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center pb-8 border-b border-white/10 gap-6">
          <ul className="flex flex-wrap gap-8 text-xs font-medium text-slate-300">
            <li><a href="#" className="hover:text-white transition-colors">О портале</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Поставщикам</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Новости</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Контакты</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Карта сайта</a></li>
          </ul>

          <div className="flex flex-col space-y-2 text-xs">
            <a href="#" className="flex items-center text-slate-300 hover:text-white transition-colors">
              🎧 Служба качества
            </a>
            <a href="#" className="flex items-center text-slate-300 hover:text-white transition-colors">
              ✉️ Написать в службу поддержки
            </a>
          </div>
        </div>

        <div className="flex flex-col md:flex-row justify-between items-center pt-8 text-[11px] text-slate-400 gap-4">
          <div>© 2017-2026 2.0.5 <br />Портал Поставщиков работает в соответствии с 44-ФЗ</div>
          
          <div className="flex space-x-3">
            {['vk', 'ok', 'tg', 'yt'].map((soc) => (
              <div key={soc} className="w-8 h-8 rounded-full bg-[#cc1f14] hover:bg-[#b0170e] transition-colors flex items-center justify-center text-white font-bold cursor-pointer">
                {soc.toUpperCase()}
              </div>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};