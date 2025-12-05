classdef ExportManager < handle
    % ExportManager - Handles export operations for behavioral video data
    %
    % This class manages various export operations including integration
    % matrices, videos, and data exports.
    %
    % Methods:
    %   exportIntegrationMatrix - Generate stimulus response matrix
    %   exportVideo             - Export video (future implementation)
    %
    % Example:
    %   em = ExportManager();
    %   em.exportIntegrationMatrix(renderer, data, track_idx, output_path);
    %
    % See also: BehavioralVideoExplorer, DataManager, Renderer
    %
    % 2025-10-16 - Refactored from IntegrationMatrixRenderer.m
    
    methods
        function obj = ExportManager()
            % Constructor - initialize export manager
        end
        
        % External method signatures (implemented in separate files)
        exportIntegrationMatrix(obj, renderer, data, track_idx, output_path)
    end
end

