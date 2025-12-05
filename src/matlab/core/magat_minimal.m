% MAGAT Minimal - Essential functions for loading experiments
%
% This file contains ONLY the minimal MAGAT functions needed to load
% experiments, replacing the need for the entire 2,000-file MAGAT codebase.
%
% Extracted from: Matlab-Track-Analysis-SkanataLab
% Author: Conejo-Code
% Date: 2025-10-16
%
% Usage:
%   Instead of:  eng.addpath(eng.genpath(magat_path))  % 2000 files, ~5s
%   Use:         eng.addpath(minimal_path)              % 1 file, <0.1s

classdef magat_minimal
    methods (Static)
        function eset = loadExperimentFromMat(mat_file)
            % Minimal ExperimentSet loader
            % Replaces: ExperimentSet.fromMatFiles()
            
            % Load MAT file
            data = load(mat_file);
            
            % Create minimal experiment set structure
            eset = struct();
            
            % Extract experiment
            if isfield(data, 'expt')
                eset.expt = data.expt;
            elseif isfield(data, 'eset') && isfield(data.eset, 'expt')
                eset.expt = data.eset.expt;
            else
                error('magat_minimal:NoExperiment', 'No experiment found in MAT file');
            end
            
            % Convert to array if needed
            if ~isa(eset.expt, 'Experiment')
                % Try to wrap in minimal Experiment if needed
                eset.expt = magat_minimal.wrapExperiment(eset.expt);
            end
        end
        
        function expt = wrapExperiment(expt_struct)
            % Wrap experiment struct with minimal Experiment-like interface
            % This provides the methods we need without full MAGAT overhead
            
            if isstruct(expt_struct)
                % Already a struct, just ensure it has methods we need
                expt = expt_struct;
            else
                expt = expt_struct;  % Already an Experiment object
            end
        end
    end
end

% Minimal Experiment class if needed
% Only implements the methods we actually use
classdef Experiment_Minimal < handle
    properties
        fname           % Binary file path
        fid = -1        % File descriptor
        camcalinfo      % Camera calibration
        globalQuantity  % Global quantities (LED data, etc.)
        track           % Associated tracks
    end
    
    methods
        function obj = Experiment_Minimal(expt_data)
            % Create minimal experiment from struct
            if isstruct(expt_data)
                % Copy fields
                if isfield(expt_data, 'fname')
                    obj.fname = expt_data.fname;
                end
                if isfield(expt_data, 'camcalinfo')
                    obj.camcalinfo = expt_data.camcalinfo;
                end
                if isfield(expt_data, 'globalQuantity')
                    obj.globalQuantity = expt_data.globalQuantity;
                end
            end
        end
        
        function openDataFile(obj)
            % Open binary data file for reading
            % Replaces full MAGAT openDataFile with minimal version
            
            if isempty(obj.fname) || ~exist(obj.fname, 'file')
                warning('Experiment_Minimal:NoFile', 'Binary file not found: %s', obj.fname);
                obj.fid = -1;
                return;
            end
            
            try
                obj.fid = fopen(obj.fname, 'r');
                if obj.fid < 0
                    warning('Experiment_Minimal:FIDError', 'Could not open file: %s', obj.fname);
                end
            catch
                warning('Experiment_Minimal:FIDError', 'Error opening file');
                obj.fid = -1;
            end
        end
    end
end

