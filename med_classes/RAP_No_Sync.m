classdef RAP_No_Sync < RAP
    properties
    end

    methods
        function set_sync_arrays(obj, issue_time)

            %% Convert excel issue_time to posix time
            time_str = string(obj.Start_Date) + " " + issue_time;
            dt = datetime(time_str, 'InputFormat', 'MM/dd/yy HH:mm:ss', ...
                    'TimeZone', 'America/Indianapolis');
            obj.sync_posix = posixtime(dt);

            %% Set corresponding med time as 0
            obj.sync_med = 0;
            
            %% Add a 2nd datapoint (+1 second) to both arrays for linear fitting
            obj.sync_posix = [obj.sync_posix, obj.sync_posix+1];
            obj.sync_med = [obj.sync_med, obj.sync_med+1];
        end
    end
end