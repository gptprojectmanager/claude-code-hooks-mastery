import { initDatabase, insertEvent, getFilterOptions, getRecentEvents } from './db';
import type { HookEvent } from './types';
import { 
  createTheme, 
  updateThemeById, 
  getThemeById, 
  searchThemes, 
  deleteThemeById, 
  exportThemeById, 
  importTheme,
  getThemeStats 
} from './theme';
import { DataPipeline } from './analytics/pipeline';
import { PredictionEngine } from './analytics/predictor';
import { InsightsEngine } from './analytics/insights';
import { RecommendationEngine } from './analytics/recommendations';
import { 
  getSessionInsights,
  getSessionMetrics,
  getAllActiveSessionMetrics,
  getActiveAnomalyAlerts,
  getOptimizationRecommendations
} from './analytics-db';

// Initialize database
initDatabase();

// Initialize analytics components
const dataPipeline = new DataPipeline();
const predictionEngine = new PredictionEngine();
const insightsEngine = new InsightsEngine();
const recommendationEngine = new RecommendationEngine();

// Initialize prediction engine
predictionEngine.initialize().then(() => {
  console.log('✅ Analytics system initialized');
}).catch(error => {
  console.error('❌ Failed to initialize analytics system:', error);
});

// Store WebSocket clients
const wsClients = new Set<any>();

// Periodic analytics processing
setInterval(async () => {
  try {
    await insightsEngine.generateInsights();
    console.log('📊 Periodic insights generated');
  } catch (error) {
    console.error('Error generating periodic insights:', error);
  }
}, 300000); // Every 5 minutes

// Create Bun server with HTTP and WebSocket support
const server = Bun.serve({
  port: 4000,
  
  async fetch(req: Request) {
    const url = new URL(req.url);
    
    // Handle CORS
    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    
    // Handle preflight
    if (req.method === 'OPTIONS') {
      return new Response(null, { headers });
    }
    
    // POST /events - Receive new events (Enhanced with analytics)
    if (url.pathname === '/events' && req.method === 'POST') {
      try {
        const event: HookEvent = await req.json();
        
        // Validate required fields
        if (!event.source_app || !event.session_id || !event.hook_event_type || !event.payload) {
          return new Response(JSON.stringify({ error: 'Missing required fields' }), {
            status: 400,
            headers: { ...headers, 'Content-Type': 'application/json' }
          });
        }
        
        // Insert event into database
        const savedEvent = insertEvent(event);
        
        // Process event through analytics pipeline
        await dataPipeline.processEvent(savedEvent);
        
        // Broadcast to all WebSocket clients with analytics data
        const message = JSON.stringify({ 
          type: 'event', 
          data: savedEvent,
          analytics: {
            sessionMetrics: getSessionMetrics(savedEvent.session_id),
            timestamp: Date.now()
          }
        });
        
        wsClients.forEach(client => {
          try {
            client.send(message);
          } catch (err) {
            // Client disconnected, remove from set
            wsClients.delete(client);
          }
        });
        
        return new Response(JSON.stringify(savedEvent), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error processing event:', error);
        return new Response(JSON.stringify({ error: 'Invalid request' }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // Analytics API Endpoints
    
    // GET /analytics/insights - Get current session insights
    if (url.pathname === '/analytics/insights' && req.method === 'GET') {
      const sessionId = url.searchParams.get('sessionId');
      const limit = parseInt(url.searchParams.get('limit') || '20');
      
      const insights = getSessionInsights(sessionId || undefined, limit);
      return new Response(JSON.stringify({
        success: true,
        data: insights,
        count: insights.length
      }), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }

    // GET /analytics/predictions - Get ML predictions for active session
    if (url.pathname === '/analytics/predictions' && req.method === 'GET') {
      const sessionId = url.searchParams.get('sessionId');
      
      if (!sessionId) {
        return new Response(JSON.stringify({
          success: false,
          error: 'Session ID is required'
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }

      try {
        const predictions = await predictionEngine.generateRealTimePredictions(sessionId);
        return new Response(JSON.stringify({
          success: true,
          data: predictions,
          count: predictions.length
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error generating predictions:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to generate predictions'
        }), {
          status: 500,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /analytics/session-metrics - Get session metrics
    if (url.pathname === '/analytics/session-metrics' && req.method === 'GET') {
      const sessionId = url.searchParams.get('sessionId');
      
      if (sessionId) {
        const metrics = getSessionMetrics(sessionId);
        return new Response(JSON.stringify({
          success: true,
          data: metrics
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } else {
        const allMetrics = getAllActiveSessionMetrics();
        return new Response(JSON.stringify({
          success: true,
          data: allMetrics,
          count: allMetrics.length
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /analytics/recommendations - Get optimization suggestions
    if (url.pathname === '/analytics/recommendations' && req.method === 'GET') {
      const sessionId = url.searchParams.get('sessionId');
      
      try {
        const recommendations = sessionId 
          ? await recommendationEngine.getSessionRecommendations(sessionId)
          : await recommendationEngine.generateRecommendations();
        
        return new Response(JSON.stringify({
          success: true,
          data: recommendations,
          count: recommendations.length
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error generating recommendations:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to generate recommendations'
        }), {
          status: 500,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /analytics/anomalies - Get anomaly alerts
    if (url.pathname === '/analytics/anomalies' && req.method === 'GET') {
      const alerts = getActiveAnomalyAlerts();
      return new Response(JSON.stringify({
        success: true,
        data: alerts,
        count: alerts.length
      }), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }

    // GET /analytics/dashboard - Get comprehensive dashboard data
    if (url.pathname === '/analytics/dashboard' && req.method === 'GET') {
      try {
        const [
          insights,
          activeMetrics,
          anomalies,
          recommendations,
          modelMetrics
        ] = await Promise.all([
          getSessionInsights(undefined, 10),
          getAllActiveSessionMetrics(),
          getActiveAnomalyAlerts(),
          recommendationEngine.generateRecommendations(),
          predictionEngine.getModelMetrics()
        ]);

        return new Response(JSON.stringify({
          success: true,
          data: {
            insights: insights.slice(0, 5),
            sessionMetrics: activeMetrics.slice(0, 10),
            anomalies: anomalies.slice(0, 5),
            recommendations: recommendations.slice(0, 3),
            modelPerformance: modelMetrics,
            summary: {
              activeSessions: activeMetrics.length,
              totalInsights: insights.length,
              activeAnomalies: anomalies.length,
              availableRecommendations: recommendations.length
            }
          }
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error generating dashboard data:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to generate dashboard data'
        }), {
          status: 500,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // POST /analytics/train - Trigger model retraining
    if (url.pathname === '/analytics/train' && req.method === 'POST') {
      try {
        // Trigger background training
        predictionEngine.trainModels().then(() => {
          console.log('✅ Model training completed');
        }).catch(error => {
          console.error('❌ Model training failed:', error);
        });

        return new Response(JSON.stringify({
          success: true,
          message: 'Model training started'
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to start model training'
        }), {
          status: 500,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // GET /analytics/quality - Get session quality metrics
    if (url.pathname === '/analytics/quality' && req.method === 'GET') {
      const sessionId = url.searchParams.get('sessionId');
      
      if (!sessionId) {
        return new Response(JSON.stringify({
          success: false,
          error: 'Session ID is required'
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }

      try {
        const qualityMetrics = await insightsEngine.calculateSessionQuality(sessionId);
        return new Response(JSON.stringify({
          success: true,
          data: qualityMetrics
        }), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error calculating quality metrics:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to calculate quality metrics'
        }), {
          status: 500,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // Original endpoints (preserved)
    
    // GET /events/filter-options - Get available filter options
    if (url.pathname === '/events/filter-options' && req.method === 'GET') {
      const options = getFilterOptions();
      return new Response(JSON.stringify(options), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /events/recent - Get recent events
    if (url.pathname === '/events/recent' && req.method === 'GET') {
      const limit = parseInt(url.searchParams.get('limit') || '100');
      const events = getRecentEvents(limit);
      return new Response(JSON.stringify(events), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // Theme API endpoints (preserved)
    
    // POST /api/themes - Create a new theme
    if (url.pathname === '/api/themes' && req.method === 'POST') {
      try {
        const themeData = await req.json();
        const result = await createTheme(themeData);
        
        const status = result.success ? 201 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error creating theme:', error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Invalid request body' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // GET /api/themes - Search themes
    if (url.pathname === '/api/themes' && req.method === 'GET') {
      const query = {
        query: url.searchParams.get('query') || undefined,
        isPublic: url.searchParams.get('isPublic') ? url.searchParams.get('isPublic') === 'true' : undefined,
        authorId: url.searchParams.get('authorId') || undefined,
        sortBy: url.searchParams.get('sortBy') as any || undefined,
        sortOrder: url.searchParams.get('sortOrder') as any || undefined,
        limit: url.searchParams.get('limit') ? parseInt(url.searchParams.get('limit')!) : undefined,
        offset: url.searchParams.get('offset') ? parseInt(url.searchParams.get('offset')!) : undefined,
      };
      
      const result = await searchThemes(query);
      return new Response(JSON.stringify(result), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /api/themes/:id - Get a specific theme
    if (url.pathname.startsWith('/api/themes/') && req.method === 'GET') {
      const id = url.pathname.split('/')[3];
      if (!id) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Theme ID is required' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      const result = await getThemeById(id);
      const status = result.success ? 200 : 404;
      return new Response(JSON.stringify(result), {
        status,
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // PUT /api/themes/:id - Update a theme
    if (url.pathname.startsWith('/api/themes/') && req.method === 'PUT') {
      const id = url.pathname.split('/')[3];
      if (!id) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Theme ID is required' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      try {
        const updates = await req.json();
        const result = await updateThemeById(id, updates);
        
        const status = result.success ? 200 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error updating theme:', error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Invalid request body' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // DELETE /api/themes/:id - Delete a theme
    if (url.pathname.startsWith('/api/themes/') && req.method === 'DELETE') {
      const id = url.pathname.split('/')[3];
      if (!id) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Theme ID is required' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      const authorId = url.searchParams.get('authorId');
      const result = await deleteThemeById(id, authorId || undefined);
      
      const status = result.success ? 200 : (result.error?.includes('not found') ? 404 : 403);
      return new Response(JSON.stringify(result), {
        status,
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /api/themes/:id/export - Export a theme
    if (url.pathname.match(/^\/api\/themes\/[^\/]+\/export$/) && req.method === 'GET') {
      const id = url.pathname.split('/')[3];
      
      const result = await exportThemeById(id);
      if (!result.success) {
        const status = result.error?.includes('not found') ? 404 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify(result.data), {
        headers: { 
          ...headers, 
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="${result.data.theme.name}.json"`
        }
      });
    }
    
    // POST /api/themes/import - Import a theme
    if (url.pathname === '/api/themes/import' && req.method === 'POST') {
      try {
        const importData = await req.json();
        const authorId = url.searchParams.get('authorId');
        
        const result = await importTheme(importData, authorId || undefined);
        
        const status = result.success ? 201 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error importing theme:', error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Invalid import data' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // GET /api/themes/stats - Get theme statistics
    if (url.pathname === '/api/themes/stats' && req.method === 'GET') {
      const result = await getThemeStats();
      return new Response(JSON.stringify(result), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // WebSocket upgrade
    if (url.pathname === '/stream') {
      const success = server.upgrade(req);
      if (success) {
        return undefined;
      }
    }
    
    // Default response
    return new Response('Multi-Agent Observability Server with Advanced Analytics', {
      headers: { ...headers, 'Content-Type': 'text/plain' }
    });
  },
  
  websocket: {
    open(ws) {
      console.log('WebSocket client connected');
      wsClients.add(ws);
      
      // Send recent events and analytics data on connection
      const events = getRecentEvents(20);
      const activeMetrics = getAllActiveSessionMetrics();
      const recentInsights = getSessionInsights(undefined, 5);
      
      ws.send(JSON.stringify({ 
        type: 'initial', 
        data: {
          events,
          sessionMetrics: activeMetrics,
          insights: recentInsights
        }
      }));
    },
    
    message(ws, message) {
      // Handle client messages for real-time analytics requests
      try {
        const request = JSON.parse(message.toString());
        
        if (request.type === 'get-predictions' && request.sessionId) {
          predictionEngine.generateRealTimePredictions(request.sessionId)
            .then(predictions => {
              ws.send(JSON.stringify({
                type: 'predictions',
                sessionId: request.sessionId,
                data: predictions
              }));
            })
            .catch(error => {
              console.error('Error generating real-time predictions:', error);
            });
        }
        
        if (request.type === 'get-recommendations' && request.sessionId) {
          recommendationEngine.getSessionRecommendations(request.sessionId)
            .then(recommendations => {
              ws.send(JSON.stringify({
                type: 'recommendations',
                sessionId: request.sessionId,
                data: recommendations
              }));
            })
            .catch(error => {
              console.error('Error generating real-time recommendations:', error);
            });
        }
        
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    },
    
    close(ws) {
      console.log('WebSocket client disconnected');
      wsClients.delete(ws);
    },
    
    error(ws, error) {
      console.error('WebSocket error:', error);
      wsClients.delete(ws);
    }
  }
});

console.log(`🚀 Server running on http://localhost:${server.port}`);
console.log(`📊 WebSocket endpoint: ws://localhost:${server.port}/stream`);
console.log(`📮 POST events to: http://localhost:${server.port}/events`);
console.log(`🧠 Analytics API: http://localhost:${server.port}/analytics/*`);
console.log(`📋 Dashboard: http://localhost:${server.port}/analytics/dashboard`);