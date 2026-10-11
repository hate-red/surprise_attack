import { Suspense } from 'react';
import { Header } from '@/widgets/header/ui/header';
import { Footer } from '@/widgets/footer/ui/footer';
import { BatchItemView } from '@/widgets/batch-item/ui/batch-item-view';

// Страница строки CSV-пакета: описание товара и интерфейс заполнения спецификации.
// useParams в клиентском компоненте требует Suspense при включённых cacheComponents.
export default function BatchItemPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans transition-colors">
      <Header />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
        <Suspense fallback={<p className="text-xs text-slate-400">Загрузка…</p>}>
          <BatchItemView />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
