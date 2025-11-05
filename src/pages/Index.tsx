import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

interface BotInfo {
  id: number;
  first_name: string;
  username: string;
}

export default function Index() {
  const [apiToken, setApiToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [botInfo, setBotInfo] = useState<BotInfo | null>(null);
  const [error, setError] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('https://functions.poehali.dev/87fade88-5166-41ab-af98-b68f978b76a8');
  const [webhookSetupDone, setWebhookSetupDone] = useState(false);
  const { toast } = useToast();

  const handleTokenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!apiToken.trim()) {
      setError('Введите API токен');
      return;
    }

    setIsLoading(true);
    setError('');
    setBotInfo(null);

    try {
      const response = await fetch('https://functions.poehali.dev/a32a9e48-7851-4521-a5bc-b4d5eb28b8c3', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: apiToken, webhook_url: webhookUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Ошибка проверки токена');
      }

      setBotInfo(data.bot);
      setWebhookSetupDone(true);
      toast({
        title: 'Успешно!',
        description: `Бот ${data.bot.first_name} подключен и готов к работе!`,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Неизвестная ошибка';
      setError(errorMessage);
      toast({
        variant: 'destructive',
        title: 'Ошибка',
        description: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12 animate-fade-in">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-primary rounded-2xl mb-6 shadow-lg">
              <Icon name="Bot" size={40} className="text-primary-foreground" />
            </div>
            <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Telegram Bot Builder
            </h1>
            <p className="text-xl text-muted-foreground">
              Создайте и настройте своего Telegram бота за несколько минут
            </p>
          </div>

          <div className="grid gap-6">
            <Card className="border-2 shadow-xl animate-scale-in">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Icon name="Key" size={24} className="text-primary" />
                  API Токен бота
                </CardTitle>
                <CardDescription>
                  Получите токен у @BotFather в Telegram и введите его ниже
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTokenSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="token">Токен API</Label>
                    <Input
                      id="token"
                      type="text"
                      placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                      value={apiToken}
                      onChange={(e) => setApiToken(e.target.value)}
                      className="font-mono"
                      disabled={isLoading}
                    />
                  </div>

                  {error && (
                    <Alert variant="destructive">
                      <Icon name="AlertCircle" size={16} />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  {botInfo && (
                    <Alert className="border-primary bg-primary/5">
                      <Icon name="CheckCircle2" size={16} className="text-primary" />
                      <AlertDescription className="text-primary">
                        Бот подключен: <strong>@{botInfo.username}</strong> ({botInfo.first_name})
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button 
                    type="submit" 
                    className="w-full" 
                    size="lg"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Icon name="Loader2" size={20} className="mr-2 animate-spin" />
                        Проверка токена...
                      </>
                    ) : (
                      <>
                        <Icon name="Rocket" size={20} className="mr-2" />
                        Подключить бота
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {botInfo && webhookSetupDone && (
              <Card className="border-2 shadow-xl animate-scale-in border-green-500">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Icon name="CheckCircle2" size={24} className="text-green-600" />
                    Бот активирован
                  </CardTitle>
                  <CardDescription>
                    Ваш бот @{botInfo.username} готов к работе в Telegram чатах
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Alert className="bg-blue-50 border-blue-200">
                    <Icon name="Info" size={16} className="text-blue-600" />
                    <AlertDescription className="text-blue-900">
                      <strong>Как использовать:</strong> Добавьте бота в любой Telegram чат и используйте команды.
                      Напишите <code className="bg-blue-100 px-2 py-1 rounded">/commands</code> чтобы увидеть все доступные команды.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg border">
                    <h4 className="font-semibold mb-3 flex items-center gap-2">
                      <Icon name="Crown" size={20} className="text-yellow-600" />
                      Ваши полномочия
                    </h4>
                    <div className="space-y-2 text-sm">
                      <p>✅ <strong>@Mad_SVO</strong> — Основатель (все права)</p>
                      <p>✅ <strong>@Andrian_SVO</strong> — Зам. Основателя</p>
                      <p className="text-muted-foreground mt-3">Используйте команды для управления ботом, назначения администраторов и модерации чатов.</p>
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4 pt-2">
                    <div className="bg-white p-4 rounded-lg border">
                      <h5 className="font-semibold mb-2 flex items-center gap-2">
                        <Icon name="Users" size={18} className="text-primary" />
                        Управление
                      </h5>
                      <ul className="text-sm space-y-1 text-muted-foreground">
                        <li>• Назначение рангов</li>
                        <li>• Управление чатами</li>
                        <li>• Список сотрудников</li>
                      </ul>
                    </div>
                    <div className="bg-white p-4 rounded-lg border">
                      <h5 className="font-semibold mb-2 flex items-center gap-2">
                        <Icon name="Shield" size={18} className="text-secondary" />
                        Модерация
                      </h5>
                      <ul className="text-sm space-y-1 text-muted-foreground">
                        <li>• Баны и муты</li>
                        <li>• Админка в чатах</li>
                        <li>• Глобальные баны</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {!botInfo && (
              <Card className="border-2 shadow-xl animate-scale-in">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Icon name="ListOrdered" size={24} className="text-secondary" />
                    Команды бота
                  </CardTitle>
                  <CardDescription>
                    Настройте команды для вашего бота
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-12 text-muted-foreground">
                    <Icon name="Package" size={48} className="mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Подключите бота, чтобы увидеть информацию</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="mt-8 grid md:grid-cols-3 gap-4">
            <Card className="border hover:border-primary transition-colors hover-scale">
              <CardContent className="pt-6 text-center">
                <Icon name="Zap" size={32} className="mx-auto mb-3 text-primary" />
                <h3 className="font-semibold mb-2">Быстрая настройка</h3>
                <p className="text-sm text-muted-foreground">
                  Подключите бота за несколько секунд
                </p>
              </CardContent>
            </Card>

            <Card className="border hover:border-secondary transition-colors hover-scale">
              <CardContent className="pt-6 text-center">
                <Icon name="Shield" size={32} className="mx-auto mb-3 text-secondary" />
                <h3 className="font-semibold mb-2">Безопасность</h3>
                <p className="text-sm text-muted-foreground">
                  Токены хранятся в защищенном окружении
                </p>
              </CardContent>
            </Card>

            <Card className="border hover:border-primary transition-colors hover-scale">
              <CardContent className="pt-6 text-center">
                <Icon name="Code" size={32} className="mx-auto mb-3 text-primary" />
                <h3 className="font-semibold mb-2">Простое управление</h3>
                <p className="text-sm text-muted-foreground">
                  Интуитивный интерфейс для настройки
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}