'use client'

import React from 'react';
import { useState } from 'react';
import { Search, Bell, MapPin,  Menu } from 'lucide-react';
import Image from 'next/image';
import {  Headphones, Lightbulb, Navigation, ShoppingCart, Globe } from 'lucide-react';

interface NavItem {
  id: string;
  icon: React.ReactNode;
  label: string;
  isLocation?: boolean;
}

export const Header: React.FC = () => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const navItems: NavItem[] = [
    { id: 'search', icon: <Search className="w-5 h-5 text-[#1e3a5f]" />, label: 'Поиск' },
    { id: 'support', icon: <Headphones className="w-5 h-5 text-[#1e3a5f]" />, label: 'Оставить обращение' },
    { id: 'help', icon: <Lightbulb className="w-5 h-5 text-[#1e3a5f]" />, label: 'Центр поддержки' },
    { id: 'location', icon: <Navigation className="w-5 h-5 text-[#1e3a5f]" />, label: 'г Москва', isLocation: true },
  ];
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2 font-bold text-xl text-red-600 tracking-tight">
            <Image src={'./Logo.svg'} alt='Logo' width={180} height={40}></Image>
          </div>
          <button className="flex items-center text-slate-700 hover:text-red-600 font-medium text-sm">
            <Menu className="w-5 h-5 mr-1.5" />
            Меню
          </button>
        </div>

        <div className="flex items-center space-x-6 text-sm text-slate-600">
        <div className="flex items-center h-full pr-[200px]">
        {navItems.map((item) => {
          const isHovered = hoveredId === item.id;

          return (
            <div
              key={item.id}
              onMouseEnter={() => setHoveredId(item.id)}
              onMouseLeave={() => setHoveredId(null)}
              className={`relative flex items-center h-full px-5 cursor-pointer border-r p-5 border-zinc-100 transition-colors duration-200 ${
                isHovered ? 'bg-[#f0f4f9]' : 'hover:bg-zinc-50'
              }`}
            >
              {/* Иконка всегда на месте */}
              <div className="shrink-0 flex items-center justify-center">
                {item.icon}
              </div>

              {/* Выезжающий текст с плавной анимацией ширины и прозрачности */}
              <div
                className={`overflow-hidden transition-all duration-1100 ease-in-out flex items-center ${
                  isHovered ? 'max-w-[200px] opacity-100 ml-2.5' : 'max-w-0 opacity-0 ml-0'
                }`}
              >
                <span className="text-sm font-medium text-[#1e3a5f] whitespace-nowrap">
                  {item.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
          
          <div className="relative">
            <Bell className="w-5 h-5 text-slate-600 cursor-pointer hover:text-red-600" />
            <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">3</span>
          </div>

          <div className="flex items-center space-x-2 pl-4 border-l border-slate-200">
            <div className="text-right">
              <div className="font-semibold text-slate-900 text-xs">Александр Семёнов</div>
              <div className="text-[10px] text-slate-400">ПО «Восход»</div>
            </div>
            <div className="w-9 h-9 bg-slate-300 rounded-full overflow-hidden flex items-center justify-center text-slate-700 font-bold text-xs">
              АС
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};