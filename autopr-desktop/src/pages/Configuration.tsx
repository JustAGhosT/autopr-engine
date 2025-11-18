import React, { useState, useEffect } from 'react';
import Form from '@rjsf/shadcn';
import { RJSFSchema } from '@rjsf/utils';
import { IChangeEvent } from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
import schema from '../schema.json';
import { invoke } from '@tauri-apps/api/core';
import yaml from 'js-yaml';
import { Button } from '../components/ui/button';

const Configuration: React.FC = () => {
  const [formData, setFormData] = useState<any>({});
  const [initialFormData, setInitialFormData] = useState<any>({});
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    invoke('read_config').then((res) => {
      const data = yaml.load(res as string);
      setFormData(data);
      setInitialFormData(data);
    });
  }, []);

  const handleSubmit = (e: IChangeEvent) => {
    invoke('write_config', { config: yaml.dump(e.formData) }).then(() => {
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    });
  };

  const handleReset = () => {
    setFormData(initialFormData);
  };

  return (
    <div>
      <h1 className="text-3xl font-bold">Configuration</h1>
      <p className="mt-2 text-gray-600">
        This page allows you to edit the AutoPR engine's configuration.
      </p>
      <div className="mt-6">
        <Form
          schema={schema as RJSFSchema}
          validator={validator}
          formData={formData}
          onChange={(e) => setFormData(e.formData)}
          onSubmit={handleSubmit}
        >
          <div className="mt-6 flex justify-end">
            <Button variant="outline" onClick={handleReset} className="mr-4">
              Reset
            </Button>
            <Button type="submit">{isSaved ? 'Saved!' : 'Save'}</Button>
          </div>
        </Form>
      </div>
    </div>
  );
};

export default Configuration;
