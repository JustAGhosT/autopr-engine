import React, { useState, useEffect } from 'react';
import Form from '@rjsf/shadcn';
import { RJSFSchema } from '@rjsf/utils';
import { IChangeEvent } from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import schema from '../schema.json';
import { invoke } from '@tauri-apps/api/core';
import yaml from 'js-yaml';
import { Button } from '../components/ui/button';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

// Toast notification component
const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
  const Icon = type === 'success' ? CheckCircle : AlertCircle;

  return (
    <div className={`fixed top-4 right-4 ${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 z-50`}>
      <Icon className="w-5 h-5" />
      <span>{message}</span>
    </div>
  );
};

const Configuration: React.FC = () => {
  const [formData, setFormData] = useState<any>({});
  const [initialFormData, setInitialFormData] = useState<any>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await invoke('read_config');
        const data = yaml.load(res as string);
        setFormData(data);
        setInitialFormData(data);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to load configuration:', error);
        showToast('Failed to load configuration', 'error');
        setIsLoading(false);
      }
    };
    loadConfig();
  }, []);

  useEffect(() => {
    // Detect if there are unsaved changes
    setHasChanges(JSON.stringify(formData) !== JSON.stringify(initialFormData));
  }, [formData, initialFormData]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges]);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
  };

  const handleSubmit = async (e: IChangeEvent) => {
    setIsSaving(true);
    try {
      await invoke('write_config', { config: yaml.dump(e.formData) });
      setInitialFormData(e.formData);
      showToast('Configuration saved successfully', 'success');
    } catch (error) {
      console.error('Failed to save configuration:', error);
      showToast('Failed to save configuration', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setFormData(initialFormData);
    showToast('Configuration reset', 'success');
  };

  // Keyboard shortcut for save
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (hasChanges && !isSaving) {
          handleSubmit({ formData } as IChangeEvent);
        }
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [formData, hasChanges, isSaving]);

  return (
    <div className="dark:text-white">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Configuration</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Edit the AutoPR engine's configuration
          {hasChanges && (
            <span className="ml-2 text-orange-600 dark:text-orange-400">
              (Unsaved changes)
            </span>
          )}
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600 dark:text-gray-400">Loading configuration...</span>
        </div>
      ) : (
        <div className="mt-6">
          <Form
            schema={schema as RJSFSchema}
            validator={validator}
            formData={formData}
            onChange={(e) => setFormData(e.formData)}
            onSubmit={handleSubmit}
            className="dark:text-gray-900"
          >
            <div className="mt-6 flex justify-end gap-4">
              <Button 
                variant="outline" 
                onClick={handleReset} 
                disabled={!hasChanges || isSaving}
                title="Reset to last saved configuration"
              >
                Reset
              </Button>
              <Button 
                type="submit" 
                disabled={!hasChanges || isSaving}
                title="Save configuration (Ctrl+S)"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Save'
                )}
              </Button>
            </div>
          </Form>
        </div>
      )}
    </div>
  );
};

export default Configuration;
