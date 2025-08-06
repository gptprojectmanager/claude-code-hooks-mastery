#!/usr/bin/env bun

/**
 * ML Model Training Script
 * 
 * This script trains the machine learning models used for session prediction
 * and analytics. It should be run periodically to update models with new data.
 */

import { PredictionEngine } from './predictor';
import { DataPipeline } from './pipeline';
import { initAnalyticsDatabase } from '../analytics-db';
import { Database } from 'bun:sqlite';

class ModelTrainer {
  private predictionEngine: PredictionEngine;
  private dataPipeline: DataPipeline;
  private db: Database;

  constructor() {
    this.predictionEngine = new PredictionEngine();
    this.dataPipeline = new DataPipeline();
    this.db = new Database('events.db');
  }

  async initialize(): Promise<void> {
    console.log('🚀 Initializing model training system...');
    
    // Initialize analytics database
    initAnalyticsDatabase();
    
    // Initialize prediction engine
    await this.predictionEngine.initialize();
    
    console.log('✅ Initialization complete');
  }

  async trainModels(): Promise<void> {
    try {
      console.log('📊 Starting model training process...');
      
      // Step 1: Prepare training data
      console.log('🔄 Processing historical data...');
      await this.dataPipeline.batchProcessHistoricalData();
      
      // Step 2: Train ML models
      console.log('🧠 Training machine learning models...');
      await this.predictionEngine.trainModels();
      
      // Step 3: Validate model performance
      console.log('📈 Validating model performance...');
      const metrics = await this.predictionEngine.getModelMetrics();
      this.reportModelMetrics(metrics);
      
      // Step 4: Update model metadata
      await this.updateModelMetadata(metrics);
      
      console.log('✅ Model training completed successfully');
      
    } catch (error) {
      console.error('❌ Error during model training:', error);
      process.exit(1);
    }
  }

  private reportModelMetrics(metrics: { [key: string]: any }): void {
    console.log('\n📊 Model Performance Metrics:');
    console.log('='.repeat(50));
    
    for (const [modelType, metric] of Object.entries(metrics)) {
      console.log(`\n${modelType.toUpperCase()}:`);
      console.log(`  ├── Accuracy: ${(metric.accuracy * 100).toFixed(1)}%`);
      console.log(`  ├── Training Samples: ${metric.sampleCount}`);
      console.log(`  └── Status: ${metric.isLoaded ? '✅ Loaded' : '❌ Not Loaded'}`);
    }
    
    console.log('\n' + '='.repeat(50));
  }

  private async updateModelMetadata(metrics: { [key: string]: any }): Promise<void> {
    const stmt = this.db.prepare(`
      INSERT INTO ml_models (model_type, version, accuracy, last_trained, training_data_size, is_active, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(model_type) DO UPDATE SET
        accuracy = excluded.accuracy,
        last_trained = excluded.last_trained,
        training_data_size = excluded.training_data_size,
        created_at = excluded.created_at
    `);

    for (const [modelType, metric] of Object.entries(metrics)) {
      stmt.run(
        modelType,
        '1.0.0',
        metric.accuracy,
        Date.now(),
        metric.sampleCount,
        1,
        Date.now()
      );
    }

    console.log('📝 Updated model metadata in database');
  }

  async generateSamplePredictions(): Promise<void> {
    console.log('🔮 Generating sample predictions...');
    
    // Get active sessions
    const activeSessionsStmt = this.db.prepare(`
      SELECT session_id FROM session_metrics 
      WHERE is_active = 1 
      LIMIT 5
    `);
    
    const activeSessions = activeSessionsStmt.all() as { session_id: string }[];
    
    for (const session of activeSessions) {
      const predictions = await this.predictionEngine.generateRealTimePredictions(session.session_id);
      console.log(`  ├── Session ${session.session_id}: ${predictions.length} predictions generated`);
    }
    
    console.log('✅ Sample predictions generated');
  }

  async runDataQualityChecks(): Promise<boolean> {
    console.log('🔍 Running data quality checks...');
    
    const checks = [
      this.checkEventDataIntegrity(),
      this.checkSessionDataCompleteness(),
      this.checkFeatureDataValidity(),
      this.checkTemporalConsistency()
    ];

    const results = await Promise.all(checks);
    const allPassed = results.every(result => result);
    
    if (allPassed) {
      console.log('✅ All data quality checks passed');
    } else {
      console.log('⚠️  Some data quality checks failed');
      results.forEach((passed, index) => {
        const checkName = ['Event Integrity', 'Session Completeness', 'Feature Validity', 'Temporal Consistency'][index];
        console.log(`  ${passed ? '✅' : '❌'} ${checkName}`);
      });
    }
    
    return allPassed;
  }

  private async checkEventDataIntegrity(): Promise<boolean> {
    const stmt = this.db.prepare(`
      SELECT COUNT(*) as total,
             COUNT(CASE WHEN session_id IS NULL OR session_id = '' THEN 1 END) as missing_session_id,
             COUNT(CASE WHEN hook_event_type IS NULL OR hook_event_type = '' THEN 1 END) as missing_event_type,
             COUNT(CASE WHEN timestamp IS NULL OR timestamp = 0 THEN 1 END) as missing_timestamp
      FROM events
    `);
    
    const result = stmt.get() as any;
    
    const missingData = result.missing_session_id + result.missing_event_type + result.missing_timestamp;
    const integrityScore = 1 - (missingData / result.total);
    
    return integrityScore > 0.95; // 95% integrity threshold
  }

  private async checkSessionDataCompleteness(): Promise<boolean> {
    const stmt = this.db.prepare(`
      SELECT COUNT(*) as total,
             COUNT(CASE WHEN start_time IS NULL THEN 1 END) as missing_start_time,
             COUNT(CASE WHEN event_count = 0 THEN 1 END) as zero_events
      FROM session_metrics
    `);
    
    const result = stmt.get() as any;
    
    const incompleteData = result.missing_start_time + result.zero_events;
    const completenessScore = 1 - (incompleteData / Math.max(result.total, 1));
    
    return completenessScore > 0.90; // 90% completeness threshold
  }

  private async checkFeatureDataValidity(): Promise<boolean> {
    const stmt = this.db.prepare(`
      SELECT COUNT(*) as total,
             COUNT(CASE WHEN feature_value IS NULL THEN 1 END) as null_values,
             COUNT(CASE WHEN feature_value != feature_value THEN 1 END) as nan_values,
             COUNT(CASE WHEN ABS(feature_value) > 1e10 THEN 1 END) as extreme_values
      FROM session_features
    `);
    
    const result = stmt.get() as any;
    
    if (result.total === 0) return true; // No features yet
    
    const invalidData = result.null_values + result.nan_values + result.extreme_values;
    const validityScore = 1 - (invalidData / result.total);
    
    return validityScore > 0.85; // 85% validity threshold
  }

  private async checkTemporalConsistency(): Promise<boolean> {
    const stmt = this.db.prepare(`
      SELECT COUNT(*) as inconsistent_sessions
      FROM session_metrics sm
      JOIN events e ON sm.session_id = e.session_id
      WHERE e.timestamp < sm.start_time
    `);
    
    const result = stmt.get() as any;
    
    return result.inconsistent_sessions === 0;
  }

  async generateTrainingReport(): Promise<void> {
    console.log('\n📋 Training Report');
    console.log('='.repeat(50));
    
    // Data summary
    const dataSummary = await this.getDataSummary();
    console.log('\n📊 Data Summary:');
    console.log(`  ├── Total Events: ${dataSummary.totalEvents}`);
    console.log(`  ├── Unique Sessions: ${dataSummary.uniqueSessions}`);
    console.log(`  ├── Active Sessions: ${dataSummary.activeSessions}`);
    console.log(`  └── Training Data Span: ${dataSummary.dataSpanDays} days`);
    
    // Model summary
    const modelMetrics = await this.predictionEngine.getModelMetrics();
    const avgAccuracy = Object.values(modelMetrics)
      .reduce((sum: number, metric: any) => sum + metric.accuracy, 0) / Object.keys(modelMetrics).length;
    
    console.log('\n🧠 Model Summary:');
    console.log(`  ├── Models Trained: ${Object.keys(modelMetrics).length}`);
    console.log(`  ├── Average Accuracy: ${(avgAccuracy * 100).toFixed(1)}%`);
    console.log(`  └── Training Status: ✅ Complete`);
    
    // Recommendations
    console.log('\n💡 Recommendations:');
    if (dataSummary.totalEvents < 1000) {
      console.log('  ⚠️  Consider collecting more data for better model performance');
    }
    if (avgAccuracy < 0.7) {
      console.log('  ⚠️  Model accuracy is low, consider feature engineering improvements');
    }
    if (dataSummary.dataSpanDays < 7) {
      console.log('  ⚠️  Limited historical data, predictions may be less reliable');
    }
    if (dataSummary.totalEvents >= 1000 && avgAccuracy >= 0.7 && dataSummary.dataSpanDays >= 7) {
      console.log('  ✅ Model training is optimal, ready for production use');
    }
    
    console.log('\n' + '='.repeat(50));
  }

  private async getDataSummary(): Promise<any> {
    const eventsSummary = this.db.prepare(`
      SELECT 
        COUNT(*) as total_events,
        COUNT(DISTINCT session_id) as unique_sessions,
        MIN(timestamp) as earliest_timestamp,
        MAX(timestamp) as latest_timestamp
      FROM events
    `).get() as any;

    const activeSessionsStmt = this.db.prepare(`
      SELECT COUNT(*) as active_sessions FROM session_metrics WHERE is_active = 1
    `);
    const activeResult = activeSessionsStmt.get() as any;

    const dataSpanMs = eventsSummary.latest_timestamp - eventsSummary.earliest_timestamp;
    const dataSpanDays = Math.ceil(dataSpanMs / (1000 * 60 * 60 * 24));

    return {
      totalEvents: eventsSummary.total_events,
      uniqueSessions: eventsSummary.unique_sessions,
      activeSessions: activeResult.active_sessions,
      dataSpanDays: Math.max(dataSpanDays, 0)
    };
  }
}

// Main execution
async function main() {
  const trainer = new ModelTrainer();
  
  try {
    await trainer.initialize();
    
    // Run data quality checks first
    const dataQualityPassed = await trainer.runDataQualityChecks();
    
    if (!dataQualityPassed) {
      console.log('⚠️  Data quality issues detected. Training may produce suboptimal results.');
      console.log('   Consider investigating and fixing data quality issues before training.');
    }
    
    // Train models
    await trainer.trainModels();
    
    // Generate sample predictions to test models
    await trainer.generateSamplePredictions();
    
    // Generate comprehensive report
    await trainer.generateTrainingReport();
    
    console.log('\n🎉 Training process completed successfully!');
    process.exit(0);
    
  } catch (error) {
    console.error('\n💥 Training process failed:', error);
    process.exit(1);
  }
}

// Run if this script is executed directly
if (import.meta.main) {
  main();
}